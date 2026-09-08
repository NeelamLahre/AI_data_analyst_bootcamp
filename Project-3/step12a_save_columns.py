import joblib
X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split.pkl')
joblib.dump(list(X_train.columns), 'outputs/xgboost_feature_columns.pkl')
print(f'Saved {len(X_train.columns)} feature columns')