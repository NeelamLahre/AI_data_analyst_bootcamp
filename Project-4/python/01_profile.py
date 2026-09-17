# python/01_profile.py
import pandas as pd
from pathlib import Path

RAW = Path("data_raw/prudential_sg_raw.csv")

df = pd.read_csv(RAW, dtype=str, keep_default_na=False)

print("Rows:", len(df))
print("Columns:", df.shape[1])
print(df.head(3).T)


NULL_TOKENS = {"", " ", "NA", "N/A", "n/a", "null", "NULL",
               "None", "-", "?", "#N/A", "unknown"}

profile = pd.DataFrame({
    "non_blank": df.apply(lambda s: (~s.str.strip().isin(NULL_TOKENS)).sum()),
    "blank_like": df.apply(lambda s: s.str.strip().isin(NULL_TOKENS).sum()),
    "distinct": df.nunique(),
    "example": df.apply(lambda s: s.dropna().iloc[0] if len(s) else ""),
})
profile["blank_pct"] = (profile.blank_like / len(df) * 100).round(2)
profile.sort_values("blank_pct", ascending=False).to_csv("logs/profile_before.csv")
print(profile.sort_values("blank_pct", ascending=False).head(12))



MANDATORY = ["record_id", "customer_id", "policy_id", "product_category",
             "policy_start_date", "annual_premium_sgd"]

gaps = profile.loc[profile.index.intersection(MANDATORY)].query("blank_like > 0")
print(f"{len(gaps)} mandatory columns have missing values")
print(gaps[["blank_like", "blank_pct"]].sort_values("blank_pct", ascending=False))