import numpy as np
import joblib
from sklearn.metrics import (roc_curve, roc_auc_score, accuracy_score,
                              precision_score, recall_score, f1_score)

y_test = np.load('outputs/nn_y_test.npy')
y_prob_nn = np.load('outputs/nn_y_prob.npy')
y_prob_lstm = np.load('outputs/lstm_y_prob.npy')

results = {}
roc_data = {}
for name, y_prob in [('Neural Network', y_prob_nn), ('LSTM', y_prob_lstm)]:
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

np.savez('outputs/roc_dl.npz',
    fpr_nn=roc_data['Neural Network'][0], tpr_nn=roc_data['Neural Network'][1],
    fpr_lstm=roc_data['LSTM'][0], tpr_lstm=roc_data['LSTM'][1],
)
joblib.dump(results, 'outputs/dl_metrics.pkl')
print('Saved outputs/roc_dl.npz and outputs/dl_metrics.pkl')