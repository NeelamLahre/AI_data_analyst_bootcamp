import numpy as np
import joblib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

tree_metrics = joblib.load('outputs/tree_metrics.pkl')
dl_metrics = joblib.load('outputs/dl_metrics.pkl')
all_metrics = {**tree_metrics, **dl_metrics}

comparison_df = pd.DataFrame(all_metrics).T
comparison_df = comparison_df.sort_values('AUC-ROC', ascending=False)
print(comparison_df.to_string())
comparison_df.to_csv('outputs/model_comparison.csv')

roc_trees = np.load('outputs/roc_trees.npz')
roc_dl = np.load('outputs/roc_dl.npz')
curves = {
    'Decision Tree': (roc_trees['fpr_dt'], roc_trees['tpr_dt']),
    'Random Forest': (roc_trees['fpr_rf'], roc_trees['tpr_rf']),
    'XGBoost': (roc_trees['fpr_xgb'], roc_trees['tpr_xgb']),
    'Neural Network': (roc_dl['fpr_nn'], roc_dl['tpr_nn']),
    'LSTM': (roc_dl['fpr_lstm'], roc_dl['tpr_lstm']),
}

plt.figure(figsize=(9, 8))
for name, (fpr, tpr) in curves.items():
    auc_val = all_metrics[name]['AUC-ROC']
    plt.plot(fpr, tpr, linewidth=2, label=f'{name} (AUC={auc_val:.3f})')
plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate (Recall)')
plt.title('ROC Curve \u2014 All 5 Models Compared')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/roc_curve_comparison.png', dpi=150)
print('Saved outputs/roc_curve_comparison.png and outputs/model_comparison.csv')