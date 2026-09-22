import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report
from xgboost import XGBClassifier

from config import DATA_PROCESSED, OUTPUT_DIR, RANDOM_STATE

df = pd.read_csv(DATA_PROCESSED / "features.csv")
y = df["churn_flag_30d"]
X = df.drop(columns=["subscriber_id", "churn_flag_30d", "churn_flag_90d"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)

# --- Baseline: Logistic Regression ---
logreg = LogisticRegression(max_iter=1000, class_weight="balanced")
logreg.fit(X_train, y_train)
p_base = logreg.predict_proba(X_test)[:, 1]
print("Baseline PR-AUC:", average_precision_score(y_test, p_base))

# --- Champion: XGBoost ---
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb = XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.05,
    scale_pos_weight=scale_pos_weight / 2, eval_metric="aucpr",
    random_state=RANDOM_STATE,
)
xgb.fit(X_train, y_train)
p_champ = xgb.predict_proba(X_test)[:, 1]
print("Champion PR-AUC:", average_precision_score(y_test, p_champ))

def recall_at_top_decile(y_true, scores):
    n_top = int(len(scores) * 0.1)
    idx = np.argsort(scores)[::-1][:n_top]
    return y_true.iloc[idx].sum() / y_true.sum()

print("Baseline recall@top-decile:", recall_at_top_decile(y_test, p_base))
print("Champion recall@top-decile:", recall_at_top_decile(y_test, p_champ))


# --- Cross-validated comparison (more stable given ~220 positives in test) ---
from sklearn.model_selection import StratifiedKFold, cross_val_score
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
print("XGB CV PR-AUC:", cross_val_score(xgb, X, y, cv=cv, scoring="average_precision").mean())
print("LogReg CV PR-AUC:", cross_val_score(logreg, X, y, cv=cv, scoring="average_precision").mean())



joblib.dump(xgb, OUTPUT_DIR / "churn_model_xgb.pkl")
joblib.dump(list(X.columns), OUTPUT_DIR / "churn_model_features.pkl")


from catboost import CatBoostClassifier

cat_scores = []
for train_idx, test_idx in cv.split(X, y):
    X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
    y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]

    cat = CatBoostClassifier(iterations=300, depth=5, learning_rate=0.05,
                              class_weights=[1, scale_pos_weight], verbose=False,
                              random_state=RANDOM_STATE)
    cat.fit(X_tr, y_tr)
    p = cat.predict_proba(X_te)[:, 1]
    cat_scores.append(average_precision_score(y_te, p))

print("CatBoost CV PR-AUC:", sum(cat_scores) / len(cat_scores))