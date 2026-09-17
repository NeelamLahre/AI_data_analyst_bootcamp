# python/04_dupe_audit.py
import pandas as pd

df = pd.read_parquet("data_clean/policy_clean.parquet")
print("Total rows:", len(df))

def fingerprint(s):
    return s.fillna("").str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)

# 1. Sanity check -- exact duplicates and policy_id uniqueness (should both be 0)
print("\nExact duplicate rows:", df.duplicated().sum())
print("Duplicate policy_id:", df.policy_id.duplicated().sum())

# 2. Same person (name + DOB), DIFFERENT policy_id -- Stage 4's fingerprint
#    required policy_id to match too, so this catches cases where the same
#    customer was resubmitted under two different policy_id values.
dob_key = pd.to_datetime(df.date_of_birth, errors="coerce").dt.strftime("%Y%m%d").fillna("")
person_key = fingerprint(df.customer_name) + "|" + dob_key
person_dupes = df[person_key.duplicated(keep=False) & (person_key != "|")]
groups = person_dupes.groupby(person_key.loc[person_dupes.index]).policy_id.nunique()
multi_policy_same_person = groups[groups > 1]
print(f"\nSame name+DOB appearing under >1 policy_id: {len(multi_policy_same_person)} people, "
      f"{person_dupes.shape[0]} rows total")

# 3. Same customer_id, different policy_id -- legitimate if genuinely different
#    products, suspicious if same product+same premium (likely a true duplicate)
cust_multi = df[df.customer_id.notna() & df.duplicated(subset="customer_id", keep=False)]
suspicious = cust_multi[cust_multi.duplicated(
    subset=["customer_id", "product_category", "annual_premium_sgd"], keep=False)]
print(f"Same customer_id + same product + same premium (likely true dupes): {len(suspicious)} rows")
if len(suspicious):
    print(suspicious[["customer_id", "policy_id", "product_category",
                       "annual_premium_sgd", "last_updated_ts"]].sort_values("customer_id").head(20))



# ---- classify the 44 groups: same policy resubmitted vs. genuinely 2 policies ----
person_dupes = person_dupes.copy()
person_dupes["_pkey"] = person_key.loc[person_dupes.index]

same_policy_resubmitted = []
genuinely_multiple = []
for pkey, grp in person_dupes.groupby("_pkey"):
    if grp.product_category.nunique() == 1 and grp.annual_premium_sgd.nunique() == 1:
        same_policy_resubmitted.append(grp)
    else:
        genuinely_multiple.append(grp)

print(f"\nGroups where product + premium MATCH (likely same policy, resubmitted): {len(same_policy_resubmitted)}")
print(f"Groups where product or premium DIFFER (likely 2 real policies, keep both): {len(genuinely_multiple)}")

if same_policy_resubmitted:
    sample = pd.concat(same_policy_resubmitted).sort_values("customer_name")
    print("\nSample of likely true duplicates:")
    print(sample[["customer_name", "date_of_birth", "policy_id", "product_category",
                   "annual_premium_sgd", "policy_start_date", "last_updated_ts"]].head(20))    