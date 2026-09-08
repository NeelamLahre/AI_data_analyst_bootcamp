import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split.pkl')


rf_model = RandomForestClassifier(
    n_estimators=100,      # start at 100, not 200 — plenty of rows already give stability
    max_depth=12,
    min_samples_split=15,
    min_samples_leaf=5,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1              # use all CPU cores
)
rf_model.fit(X_train, y_train)
print('Random Forest trained!')


y_pred_rf = rf_model.predict(X_test)
y_prob_rf = rf_model.predict_proba(X_test)[:, 1]

print(f'Accuracy: {accuracy_score(y_test, y_pred_rf):.4f}')
print(f'AUC-ROC: {roc_auc_score(y_test, y_prob_rf):.4f}')
print(classification_report(y_test, y_pred_rf, target_names=['Ineffective', 'Effective']))


importance_rf = pd.Series(rf_model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
print(importance_rf.head(10))

joblib.dump(rf_model, 'outputs/random_forest_model.pkl')
print('Saved outputs/random_forest_model.pkl')