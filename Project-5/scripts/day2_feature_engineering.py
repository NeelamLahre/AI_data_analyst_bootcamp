import pandas as pd
from config import SUBSCRIBERS_CSV, DATA_PROCESSED, LEAKAGE_COLUMNS

subs = pd.read_csv(SUBSCRIBERS_CSV, parse_dates=["join_date"])
subs = subs.drop(columns=LEAKAGE_COLUMNS)

bool_cols = ["autopay_enabled", "is_5g_device", "is_5g_active", "family_plan_flag",
             "roaming_user_flag", "offer_exposed_90d", "offer_redeemed_90d"]
for c in bool_cols:
    subs[c] = subs[c].astype(int)

cat_cols = ["circle", "zone", "plan_type", "device_brand", "home_product"]
subs_encoded = pd.get_dummies(subs, columns=cat_cols, drop_first=True)
subs_encoded = subs_encoded.drop(columns=["join_date", "circle_code"])

print("Nulls remaining:\n", subs_encoded.isna().sum()[subs_encoded.isna().sum() > 0])
subs_encoded = subs_encoded.fillna(subs_encoded.median(numeric_only=True))

DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
subs_encoded.to_csv(DATA_PROCESSED / "features.csv", index=False)
print("Saved:", subs_encoded.shape)