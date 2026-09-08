import joblib
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split.pkl')

neg, pos = y_train.value_counts()[0], y_train.value_counts()[1]
scale_pos_weight = neg / pos
print(f'scale_pos_weight = {scale_pos_weight:.2f}')

xgb_model = XGBClassifier(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    eval_metric='auc',
    n_jobs=-1
)
xgb_model.fit(X_train, y_train)
print('XGBoost trained!')

y_pred_xgb = xgb_model.predict(X_test)
y_prob_xgb = xgb_model.predict_proba(X_test)[:, 1]

print(f'Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}')
print(f'AUC-ROC: {roc_auc_score(y_test, y_prob_xgb):.4f}')
print(classification_report(y_test, y_pred_xgb, target_names=['Ineffective', 'Effective']))


joblib.dump(xgb_model, 'outputs/xgboost_model.pkl')
print('Saved outputs/xgboost_model.pkl')
