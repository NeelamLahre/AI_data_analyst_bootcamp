import pandas as pd
from xgboost import XGBClassifier
from config import DATA_PROCESSED, RANDOM_STATE

df = pd.read_csv(DATA_PROCESSED / "features.csv")

treat_col = "offer_exposed_90d"
outcome = 1 - df["churn_flag_90d"]  # "retained" = 1 is the positive outcome we want the offer to cause

feature_cols = [c for c in df.columns if c not in
                ["subscriber_id", "churn_flag_30d", "churn_flag_90d", treat_col]]

treated = df[df[treat_col] == 1]
control = df[df[treat_col] == 0]
print(f"Treated: {len(treated)}, Control: {len(control)}")

def fit_model(sub_df, y_sub):
    X_sub = sub_df[feature_cols]
    m = XGBClassifier(n_estimators=200, max_depth=4, random_state=RANDOM_STATE)
    m.fit(X_sub, y_sub)
    return m

model_treated = fit_model(treated, outcome.loc[treated.index])
model_control = fit_model(control, outcome.loc[control.index])

X_all = df[feature_cols]
p_treated = model_treated.predict_proba(X_all)[:, 1]
p_control = model_control.predict_proba(X_all)[:, 1]
uplift = p_treated - p_control

result = pd.DataFrame({
    "subscriber_id": df["subscriber_id"],
    "p_retain_if_treated": p_treated,
    "p_retain_if_untreated": p_control,
    "uplift_score": uplift,
})

print(result["uplift_score"].describe())

def segment(u):
    if u > 0.05:
        return "Persuadable"
    if u < -0.02:
        return "Sleeping dog (do not disturb)"
    return "Sure thing / Lost cause"

result["segment"] = result["uplift_score"].apply(segment)
result.to_csv(DATA_PROCESSED / "uplift_scores.csv", index=False)
print(result["segment"].value_counts())