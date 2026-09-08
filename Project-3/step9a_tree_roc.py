import joblib
import numpy as np
from sklearn.metrics import (roc_curve, roc_auc_score, accuracy_score,
                              precision_score, recall_score, f1_score)

X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split.pkl')

models = {
    'Decision Tree': joblib.load('outputs/decision_tree_model.pkl'),
    'Random Forest': joblib.load('outputs/random_forest_model.pkl'),
    'XGBoost': joblib.load('outputs/xgboost_model.pkl'),
}

results = {}
roc_data = {}
for name, model in models.items():
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_data[name] = (fpr, tpr)
    results[name] = {
        'Accuracy': accuracy_score(y_test, y_pred),
        'Precision': precision_score(y_test, y_pred),
        'Recall': recall_score(y_test, y_pred),
        'F1': f1_score(y_test, y_pred),
        'AUC-ROC': roc_auc_score(y_test, y_prob),
    }
    print(name, results[name])

np.savez('outputs/roc_trees.npz',
    fpr_dt=roc_data['Decision Tree'][0], tpr_dt=roc_data['Decision Tree'][1],
    fpr_rf=roc_data['Random Forest'][0], tpr_rf=roc_data['Random Forest'][1],
    fpr_xgb=roc_data['XGBoost'][0], tpr_xgb=roc_data['XGBoost'][1],
)
joblib.dump(results, 'outputs/tree_metrics.pkl')
print('Saved outputs/roc_trees.npz and outputs/tree_metrics.pkl')