# python/03_load.py
import pandas as pd
from sqlalchemy import create_engine, text

ENGINE = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/prudential_dw"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
)

# ---- make this script safely re-runnable: clear the previous load first ----
with ENGINE.begin() as conn:
    conn.execute(text("DELETE FROM fact_claim"))
    conn.execute(text("DELETE FROM fact_policy_new_business"))
    conn.execute(text("DELETE FROM dim_date"))
    conn.execute(text("DELETE FROM dim_product"))
    conn.execute(text("DELETE FROM dim_channel"))
    conn.execute(text("DELETE FROM dim_customer"))
    conn.execute(text("DELETE FROM dim_agent"))
    conn.execute(text("DELETE FROM dim_assessor"))
    conn.execute(text("DELETE FROM dim_claim_type"))
print("Cleared previous load")


df = pd.read_parquet("data_clean/policy_clean.parquet")

df["months_inforce"] = pd.to_numeric(df.months_inforce, errors="coerce")
df["care_delay_days"] = pd.to_numeric(df.care_delay_days, errors="coerce")

# ---- 1. dim_date: build once, covering the extract's real date range ----
all_dates = pd.concat([df.policy_start_date, df.quote_date, df.claim_date, df.lapse_date]).dropna()
date_range = pd.date_range(all_dates.min().normalize(), all_dates.max().normalize(), freq="D")
dim_date = pd.DataFrame({
    "date_key":   date_range.strftime("%Y%m%d").astype(int),
    "date":       date_range,
    "year":       date_range.year,
    "quarter":    date_range.quarter,
    "month":      date_range.month,
    "year_month": date_range.strftime("%Y-%m"),
})
dim_date.to_sql("dim_date", ENGINE, if_exists="append", index=False)
print(f"Loaded {len(dim_date)} dim_date rows")

# ---- 2. simple lookup dimensions ----
dim_product = (df[["product_name", "product_category"]]
               .dropna().drop_duplicates().reset_index(drop=True))
dim_product["is_low_margin"] = dim_product.product_category.isin(
    ["Savings & Wealth", "Investment-Linked"])
dim_product.to_sql("dim_product", ENGINE, if_exists="append", index=False)

dim_channel = pd.DataFrame({"channel_name": df.distribution_channel.dropna().unique()})
dim_channel.to_sql("dim_channel", ENGINE, if_exists="append", index=False)

dim_customer = (df[["customer_id", "gender", "age", "income_band",
                     "residency_status", "occupation_group"]]
                .dropna(subset=["customer_id"]).drop_duplicates(subset="customer_id"))
dim_customer.to_sql("dim_customer", ENGINE, if_exists="append", index=False)

# ---- 3. dim_agent (first load -- every agent starts as the current version) ----
dim_agent = (df[["agent_id", "agent_name", "agent_tier", "agency_unit",
                  "agent_status", "agent_attrition_risk"]]
             .rename(columns={"agent_attrition_risk": "attrition_risk"})
             .dropna(subset=["agent_id"]).drop_duplicates(subset="agent_id"))
dim_agent["valid_from"] = df.policy_start_date.min()
dim_agent["valid_to"] = pd.Timestamp("9999-12-31")
dim_agent["is_current"] = True
dim_agent.to_sql("dim_agent", ENGINE, if_exists="append", index=False)

print("Dimensions loaded.")

# ---- 4. attach surrogate keys, then load the fact ----
product_keys  = pd.read_sql("SELECT product_key, product_name, product_category FROM dim_product", ENGINE)
channel_keys  = pd.read_sql("SELECT channel_key, channel_name FROM dim_channel", ENGINE)
customer_keys = pd.read_sql("SELECT customer_key, customer_id FROM dim_customer", ENGINE)
agent_keys    = pd.read_sql("SELECT agent_key, agent_id FROM dim_agent WHERE is_current = 1", ENGINE)
date_keys     = pd.read_sql("SELECT date_key, [date] FROM dim_date", ENGINE)
date_keys["date"] = pd.to_datetime(date_keys["date"])   # pyodbc returns Python date objects, not datetime64

fact = (df
        .merge(product_keys, on=["product_name", "product_category"], how="left")
        .merge(channel_keys.rename(columns={"channel_name": "distribution_channel"}),
               on="distribution_channel", how="left")
        .merge(customer_keys, on="customer_id", how="left")
        .merge(agent_keys, on="agent_id", how="left")
        .merge(date_keys.rename(columns={"date": "policy_start_date"}),
               on="policy_start_date", how="left")
        .rename(columns={"date_key": "start_date_key"}))

# ---- 5. quarantine rows that failed to match dim_product ----
# 46 rows have product_category but no product_name -- known since Stage 2 profiling
# (product_name was never on Stage 3's CRITICAL list, so it was never quarantined earlier).
# Don't guess a product_name here -- that would misattribute real premium to the wrong product.
missing_product = fact.product_key.isna()
if missing_product.any():
    fact[missing_product].assign(reject_reason="NO_PRODUCT_DIM_MATCH") \
        .to_csv("data_quarantine/q_load_no_product_match.csv", index=False)
    print(f"Quarantined {missing_product.sum()} rows -- product_category present but product_name missing")
    fact = fact[~missing_product].copy()

# ---- 6. quarantine rows that would violate the warehouse's CHECK (annual_premium_sgd > 0) ----
bad_premium = fact.annual_premium_sgd.notna() & (fact.annual_premium_sgd <= 0)
if bad_premium.any():
    fact[bad_premium].assign(reject_reason="NON_POSITIVE_PREMIUM") \
        .to_csv("data_quarantine/q_load_non_positive_premium.csv", index=False)
    print(f"Quarantined {bad_premium.sum()} rows -- annual_premium_sgd <= 0 (violates warehouse CHECK)")
    fact = fact[~bad_premium].copy()

assert fact.product_key.isna().sum() == 0, "product_key still has unmatched rows after quarantine"
assert (fact.annual_premium_sgd <= 0).sum() == 0, "non-positive premiums still present after quarantine"



# ---- 6. column naming: source data uses persistency_13m_flag, our SQL table uses persistency_13m ----
fact = fact.rename(columns={"persistency_13m_flag": "persistency_13m"})

FACT_COLS = ["policy_id", "customer_key", "product_key", "channel_key", "agent_key",
             "start_date_key", "annual_premium_sgd", "sum_assured_sgd", "ape_sgd",
             "nbp_margin_pct", "months_inforce", "lapse_flag", "persistency_13m",
             "care_delay_days", "copay_pct", "dq_row_status"]

fact[FACT_COLS].to_sql("fact_policy_new_business", ENGINE,
                        if_exists="append", index=False, chunksize=1000)
print(f"Loaded {len(fact):,} policy rows")