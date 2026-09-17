# python/03b_load_claims.py
import pandas as pd
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/prudential_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

df = pd.read_parquet("data_clean/policy_clean.parquet")
df["claim_tat_days"] = pd.to_numeric(df.claim_tat_days, errors="coerce")

claims = df[df.claim_id.notna()].copy()
print(f"{len(claims):,} rows have a claim_id out of {len(df):,} total")

# ---- de-dupe claim_id, same survivor rule as Stage 4 (most recently updated wins) ----
dupe_claim = claims.claim_id.duplicated(keep=False)
if dupe_claim.any():
    print(f"{dupe_claim.sum()} rows share a claim_id with another row -- deduping, keep most recent")
    claims = claims.sort_values("last_updated_ts", ascending=True)
    keep_mask = ~claims.duplicated(subset="claim_id", keep="last")
    claims[~keep_mask].assign(reject_reason="DUPLICATE_CLAIM_ID") \
        .to_csv("data_quarantine/q_claim_duplicate_id.csv", index=False)
    claims = claims[keep_mask].copy()

# ---- 1. dim_claim_type -- normalise casing/whitespace, never standardised earlier ----
claims["claim_type"] = claims.claim_type.str.strip().str.title()
dim_claim_type = pd.DataFrame({"claim_type": claims.claim_type.dropna().unique()})
dim_claim_type.to_sql("dim_claim_type", ENGINE, if_exists="append", index=False)
print(f"Loaded {len(dim_claim_type)} dim_claim_type rows")

# ---- 2. dim_assessor ----
dim_assessor = (claims[["assessor_id", "assessor_approval_limit_sgd"]]
                .dropna(subset=["assessor_id"])
                .drop_duplicates(subset="assessor_id"))
dim_assessor.to_sql("dim_assessor", ENGINE, if_exists="append", index=False)
print(f"Loaded {len(dim_assessor)} dim_assessor rows")

# ---- 3. attach surrogate keys ----
policy_keys     = pd.read_sql("SELECT policy_key, policy_id FROM fact_policy_new_business", ENGINE)
assessor_keys   = pd.read_sql("SELECT assessor_key, assessor_id FROM dim_assessor", ENGINE)
claim_type_keys = pd.read_sql("SELECT claim_type_key, claim_type FROM dim_claim_type", ENGINE)
date_keys       = pd.read_sql("SELECT date_key, [date] FROM dim_date", ENGINE)
date_keys["date"] = pd.to_datetime(date_keys["date"])

fact_claim = (claims
              .merge(policy_keys, on="policy_id", how="left")
              .merge(assessor_keys, on="assessor_id", how="left")
              .merge(claim_type_keys, on="claim_type", how="left")
              .merge(date_keys.rename(columns={"date": "claim_date"}),
                     on="claim_date", how="left")
              .rename(columns={"date_key": "claim_date_key",
                                "approval_above_limit_flag": "approval_above_limit",
                                "sod_breach_flag": "sod_breach"}))

# ---- 4. quarantine claims whose policy was itself quarantined at Stage 8 ----
orphan_policy = fact_claim.policy_key.isna()
if orphan_policy.any():
    fact_claim[orphan_policy].assign(reject_reason="POLICY_NOT_LOADED") \
        .to_csv("data_quarantine/q_claim_orphan_policy.csv", index=False)
    print(f"Quarantined {orphan_policy.sum()} claims -- parent policy was itself quarantined")
    fact_claim = fact_claim[~orphan_policy].copy()

assert fact_claim.policy_key.isna().sum() == 0, "policy_key still has unmatched rows after quarantine"

CLAIM_COLS = ["claim_id", "policy_key", "assessor_key", "claim_type_key", "claim_date_key",
              "claim_amount_sgd", "claim_tat_days", "claim_status", "claim_decline_reason",
              "approval_above_limit", "sod_breach", "fraud_risk_score",
              "disputed_flag", "complaint_flag", "dq_row_status"]

fact_claim[CLAIM_COLS].to_sql("fact_claim", ENGINE, if_exists="append", index=False, chunksize=1000)
print(f"Loaded {len(fact_claim):,} claim rows")