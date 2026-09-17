# python/02_clean.py
import numpy as np
import pandas as pd
from pathlib import Path

df = pd.read_csv("data_raw/prudential_sg_raw.csv", dtype=str, keep_default_na=False)
audit = []  # running log of every change we make

NULL_TOKENS = {"", " ", "NA", "N/A", "n/a", "null", "NULL",
               "None", "-", "?", "#N/A", "unknown"}

df = df.apply(lambda s: s.str.strip())
df = df.mask(df.isin(NULL_TOKENS))

audit.append(("null_standardised", int(df.isna().sum().sum())))
print("Cells now genuinely null:", df.isna().sum().sum())


dob = pd.to_datetime(df.date_of_birth, errors="coerce", format="mixed", dayfirst=True)
derived_age = ((pd.Timestamp("2026-09-01") - dob).dt.days / 365.25).round().astype("Int64")

df["age"] = pd.to_numeric(df.age, errors="coerce").astype("Int64")

implausible = df.age.notna() & ~df.age.between(0, 120)
n_implausible = int(implausible.sum())
df.loc[implausible, "age"] = pd.NA
audit.append(("age_implausible_discarded", n_implausible))

filled = df.age.isna() & derived_age.notna()
df.loc[filled, "age"] = derived_age[filled]
audit.append(("age_derived_from_dob", int(filled.sum())))



for col in ["occupation_group", "postal_district", "marital_status", "residency_status"]:
    mode = df[col].mode()
    if not mode.empty:
        n = int(df[col].isna().sum())
        df[col] = df[col].fillna(mode[0])
        df[f"{col}_imputed_flag"] = False
        audit.append((f"{col}_imputed", n))



CRITICAL = ["policy_id", "customer_id", "annual_premium_sgd",
            "product_category", "policy_start_date"]

bad = df[CRITICAL].isna().any(axis=1)
quarantine = df[bad].copy()
quarantine["reject_reason"] = "MISSING_CRITICAL_FIELD"
quarantine.to_csv("data_quarantine/q_missing_critical.csv", index=False)

df = df[~bad].copy()
audit.append(("rows_quarantined_missing", int(bad.sum())))
print(f"Quarantined {bad.sum()} rows; {len(df)} rows continue")

df.to_parquet("data_clean/_stage3_missing_handled.parquet", index=False)

report = pd.DataFrame(audit, columns=["check", "records_affected"])
report["run_ts"] = pd.Timestamp.now()
report.to_csv("logs/dq_report_stage3.csv", index=False)
print(report.to_string(index=False))

#4.1 Exact duplicates
before = len(df)
dupe_mask = df.duplicated(keep="first")
df[dupe_mask].assign(reject_reason="EXACT_DUPLICATE") \
    .to_csv("data_quarantine/q_exact_dupes.csv", index=False)
df = df[~dupe_mask].copy()
audit.append(("exact_duplicates_removed", before - len(df)))
print(f"Removed {before - len(df)} exact duplicates")




#4.2 Fuzzy duplicates — the same person submitted twice, formatted differently

def fingerprint(text: pd.Series) -> pd.Series:
    """Reduce free text to letters and digits only, in upper case."""
    return (text.fillna("")
            .str.upper()
            .str.replace(r"[^A-Z0-9]", "", regex=True))

dob_key = pd.to_datetime(df.date_of_birth, errors="coerce",
                          format="mixed", dayfirst=True).dt.strftime("%Y%m%d")

df["_match_key"] = (fingerprint(df.policy_id) + "|" +
                     fingerprint(df.customer_name) + "|" +
                     dob_key.fillna(""))

df = df.sort_values("last_updated_ts", ascending=True)
fuzzy_mask = df.duplicated(subset="_match_key", keep="last")

df[fuzzy_mask].assign(reject_reason="FUZZY_DUPLICATE") \
    .to_csv("data_quarantine/q_fuzzy_dupes.csv", index=False)
df = df[~fuzzy_mask].drop(columns="_match_key").copy()
audit.append(("fuzzy_duplicates_removed", int(fuzzy_mask.sum())))

#4.3 Prove it worked:
assert df.duplicated().sum() == 0, "exact duplicates still present"
assert df.policy_id.duplicated().sum() == 0, "policy_id is not unique"
print("Duplicate checks passed. Rows remaining:", len(df))




#5.1 Dates — six-plus formats, one target.
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m-%d-%Y",
                 "%d-%b-%y", "%B %d, %Y", "%Y/%m/%d", "%d.%m.%Y"]

def parse_dates(series: pd.Series) -> pd.Series:
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    remaining = series.notna()
    for fmt in DATE_FORMATS:
        if not remaining.any():
            break
        attempt = pd.to_datetime(series[remaining], format=fmt, errors="coerce")
        result.loc[attempt.notna().index[attempt.notna()]] = attempt.dropna()
        remaining = remaining & result.isna()
    return result

DATE_COLS = ["date_of_birth", "quote_date", "policy_start_date", "lapse_date", "claim_date"]
for col in DATE_COLS:
    parsed = parse_dates(df[col])
    audit.append((f"{col}_unparseable", int(df[col].notna().sum() - parsed.notna().sum())))
    df[col] = parsed


#Business-rule check on dates:

EXTRACT_DATE = pd.Timestamp("2026-09-01")
bad_dates = (
    (df.policy_start_date > EXTRACT_DATE)
    | (df.policy_start_date < pd.Timestamp("1990-01-01"))
    | (df.quote_date > df.policy_start_date)
    | (df.claim_date < df.policy_start_date)
)
df.loc[bad_dates.fillna(False), "dq_flag_date"] = "DATE_LOGIC_BREACH"
audit.append(("date_logic_breaches", int(bad_dates.fillna(False).sum())))


# 5.2 Currency written as text:

def to_amount(series: pd.Series) -> pd.Series:
    cleaned = (series.astype(str)
               .str.replace(r"(?i)(SGD|S\$|\$|,|\s)", "", regex=True)
               .replace({"": None, "nan": None}))
    return pd.to_numeric(cleaned, errors="coerce")

MONEY_COLS = ["annual_premium_sgd", "sum_assured_sgd", "ape_sgd",
              "claim_amount_sgd", "annual_income_sgd", "deductible_sgd",
              "rider_premium_before_sgd", "rider_premium_after_sgd",
              "assessor_approval_limit_sgd"]
for col in MONEY_COLS:
    df[col] = to_amount(df[col])





def to_fraction(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.strip()
    is_pct = raw.str.endswith("%")
    value = pd.to_numeric(raw.str.rstrip("%"), errors="coerce")
    return value.where(~is_pct, value / 100)

df["nbp_margin_pct"] = to_fraction(df.nbp_margin_pct)
df["copay_pct"] = pd.to_numeric(df.copay_pct, errors="coerce")
df["fraud_risk_score"] = pd.to_numeric(df.fraud_risk_score, errors="coerce")




print(df[["annual_premium_sgd", "nbp_margin_pct", "policy_start_date"]].dtypes)
print(df.nbp_margin_pct.describe())




from difflib import get_close_matches

VALID = {
    "distribution_channel": ["Agency", "Bancassurance", "Digital", "Broker", "Direct"],
    "product_category":     ["Protection", "Savings & Wealth", "Health & IP", "Investment-Linked"],
    "policy_status":        ["Inforce", "Matured", "Lapsed", "Surrendered", "Cancelled"],
    "claim_status":         ["Approved", "Partially Approved", "Declined", "Pending", "Withdrawn"],
}

def standardise(series: pd.Series, allowed: list[str]) -> pd.Series:
    lookup = {a.upper(): a for a in allowed}
    def fix(v):
        if pd.isna(v):
            return None
        key = str(v).strip().upper()
        if key in lookup:
            return lookup[key]
        near = get_close_matches(key, lookup.keys(), n=1, cutoff=0.6)
        return lookup[near[0]] if near else "UNMAPPED"
    return series.map(fix)

for col, allowed in VALID.items():
    df[col] = standardise(df[col], allowed)
    audit.append((f"{col}_unmapped", int((df[col] == "UNMAPPED").sum())))






GENDER = {"M": "Male", "MALE": "Male", "F": "Female", "FEMALE": "Female", "FEMAL": "Female"}
df["gender"] = df.gender.str.strip().str.upper().map(GENDER)

TRUTHY = {"Y", "YES", "TRUE", "T", "1"}
FALSY = {"N", "NO", "FALSE", "F", "0"}
FLAG_COLS = ["lapse_flag", "rider_attached_flag", "disputed_flag", "complaint_flag",
             "chronic_condition_flag", "persistency_13m_flag", "sod_breach_flag",
             "approval_above_limit_flag"]
for col in FLAG_COLS:
    up = df[col].astype(str).str.strip().str.upper()
    df[col] = np.select([up.isin(TRUTHY), up.isin(FALSY)], [True, False], default=None)



df["claim_tat_days"] = pd.to_numeric(df.claim_tat_days, errors="coerce")

RULES = {
    "age": (18, 100), "annual_premium_sgd": (1, 250_000),
    "sum_assured_sgd": (1_000, 10_000_000), "claim_amount_sgd": (1, 1_000_000),
    "claim_tat_days": (0, 365), "copay_pct": (0, 100),
    "nbp_margin_pct": (0, 1), "fraud_risk_score": (0, 1),
}
violations = pd.Series(False, index=df.index)
for col, (low, high) in RULES.items():
    out_of_range = df[col].notna() & (~df[col].between(low, high))
    df.loc[out_of_range, f"dq_{col}"] = "OUT_OF_RANGE"
    violations = violations | out_of_range
    audit.append((f"{col}_out_of_range", int(out_of_range.sum())))

violations = violations | bad_dates.fillna(False)   # fold in Stage 5's date-logic breaches, too
df["dq_row_status"] = np.where(violations, "REVIEW", "OK")
print(df.dq_row_status.value_counts())



has_agent_id = df.agent_id.notna()
looks_fabricated = has_agent_id & df.agent_name.isna()
df.loc[looks_fabricated, "dq_agent_id"] = "ORPHAN_REFERENCE"
df.loc[looks_fabricated, "agent_id"] = "AGT-UNKNOWN"
audit.append(("orphan_agent_ids", int(looks_fabricated.sum())))



df.to_parquet("data_clean/policy_clean.parquet", index=False)
df.to_csv("data_clean/policy_clean.csv", index=False)

report = pd.DataFrame(audit, columns=["check", "records_affected"])
report["run_ts"] = pd.Timestamp.now()
report.to_csv("logs/dq_report.csv", index=False)
print(report.to_string(index=False))

