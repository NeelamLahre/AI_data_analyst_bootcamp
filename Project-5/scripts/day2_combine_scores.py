import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression

from config import DATA_PROCESSED, OUTPUT_DIR, RANDOM_STATE

df = pd.read_csv(DATA_PROCESSED / "features.csv")

# --- Churn score: refit the SELECTED model (Logistic Regression) on the full population ---
# Train/test split was only for evaluation - for the scoring table used by the Day 3-4
# chatbot, every subscriber needs a score, so fit on all the data.
y_churn = df["churn_flag_30d"]
X_churn = df.drop(columns=["subscriber_id", "churn_flag_30d", "churn_flag_90d"])

logreg_final = LogisticRegression(max_iter=2000, class_weight="balanced")
logreg_final.fit(X_churn, y_churn)
churn_scores = pd.DataFrame({
    "subscriber_id": df["subscriber_id"],
    "churn_score": logreg_final.predict_proba(X_churn)[:, 1],
})

# --- CLV: reuse the already-trained Random Forest model ---
clv_model = joblib.load(OUTPUT_DIR / "clv_model_rf.pkl")
X_clv = df.drop(columns=[
    "subscriber_id", "churn_flag_30d", "churn_flag_90d",
    "arpu_last_month_inr", "arpu_3m_avg_inr", "arpu_6m_avg_inr",
])
clv_scores = pd.DataFrame({
    "subscriber_id": df["subscriber_id"],
    "clv_predicted": clv_model.predict(X_clv),
})

# --- Uplift: already scored for the full population in day2_uplift_model.py ---
uplift_scores = pd.read_csv(DATA_PROCESSED / "uplift_scores.csv")[
    ["subscriber_id", "uplift_score", "segment"]
]

# --- Merge everything into one table ---
scored = churn_scores.merge(clv_scores, on="subscriber_id").merge(uplift_scores, on="subscriber_id")
scored.to_csv(DATA_PROCESSED / "scored_subscribers.csv", index=False)

print(scored.shape)
print(scored.head())
print(scored.describe())