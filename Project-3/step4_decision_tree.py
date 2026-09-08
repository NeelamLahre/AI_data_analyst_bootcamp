import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import pandas as pd

X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split.pkl')




object_cols = X_train.select_dtypes(include='object').columns.tolist()
print('Remaining text columns:', object_cols)
for col in object_cols:
    print(f'\n{col} sample values:')
    print(X_train[col].unique()[:20])




dt_model = DecisionTreeClassifier(
    max_depth=8,
    min_samples_split=20,
    min_samples_leaf=10,
    class_weight='balanced',
    random_state=42
)
dt_model.fit(X_train, y_train)
print('Decision Tree trained!')


y_pred = dt_model.predict(X_test)
y_prob = dt_model.predict_proba(X_test)[:, 1]

print(f'Accuracy: {accuracy_score(y_test, y_pred):.4f}')
print(f'AUC-ROC: {roc_auc_score(y_test, y_prob):.4f}')
print(classification_report(y_test, y_pred, target_names=['Ineffective', 'Effective']))


importance = pd.Series(dt_model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
print(importance.head(10))

joblib.dump(dt_model, 'outputs/decision_tree_model.pkl')
print('Saved outputs/decision_tree_model.pkl')