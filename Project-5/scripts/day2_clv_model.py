import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

from config import DATA_PROCESSED, OUTPUT_DIR, RANDOM_STATE

df = pd.read_csv(DATA_PROCESSED / "features.csv")

# Target: simple 12-month CLV projection off 6-month average ARPU
df["clv_target"] = df["arpu_6m_avg_inr"] * 12

y = df["clv_target"]
X = df.drop(columns=[
    "subscriber_id", "churn_flag_30d", "churn_flag_90d", "clv_target",
    "arpu_last_month_inr", "arpu_3m_avg_inr", "arpu_6m_avg_inr",  # drop ARPU inputs so the model can't just learn clv = arpu*12 back out
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)

# --- Baseline: Linear Regression ---
lin = LinearRegression()
lin.fit(X_train, y_train)
p_base = lin.predict(X_test)
print("Baseline MAE:", mean_absolute_error(y_test, p_base))
print("Baseline R2:", r2_score(y_test, p_base))

# --- Champion: Random Forest ---
rf = RandomForestRegressor(n_estimators=300, max_depth=10, n_jobs=-1, random_state=RANDOM_STATE)
rf.fit(X_train, y_train)
p_champ = rf.predict(X_test)
print("Champion MAE:", mean_absolute_error(y_test, p_champ))
print("Champion R2:", r2_score(y_test, p_champ))

joblib.dump(rf, OUTPUT_DIR / "clv_model_rf.pkl")

# Save predictions with subscriber_id for later merging into the combined scored table
clv_predictions = pd.DataFrame({
    "subscriber_id": df.loc[X_test.index, "subscriber_id"],
    "clv_actual": y_test,
    "clv_predicted": p_champ,
})
clv_predictions.to_csv(DATA_PROCESSED / "clv_predictions.csv", index=False)