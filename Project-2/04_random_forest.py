"""
Step 4 - Random Forest Classifier
Trains a Random Forest on the cleaned data, saves the model.
"""
import pandas as pd
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
)
from config import DATA_CLEANED, OUTPUT_DIR, TARGET, RANDOM_STATE, split_data

# Load cleaned data
df = pd.read_csv(DATA_CLEANED)
X = df.drop(columns=[TARGET])
y = df[TARGET]

# Three-way split: Train (60%) / Validation (20%) / Test (20%)
# Same RANDOM_STATE as 03_decision_tree.py -> identical split, fair comparison.
# Test is intentionally NOT touched in this file - it's saved for Step 5.
X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
print(f"Train: {X_train.shape}, Validation: {X_val.shape}, Test: {X_test.shape}")

# Create and train the Random Forest (200 trees voting together)
rf = RandomForestClassifier(
    n_estimators=200, max_depth=12, min_samples_split=10,
    random_state=RANDOM_STATE, n_jobs=-1
)
rf.fit(X_train, y_train)  # learns using ONLY the training set

# Check for overfitting/underfitting: Train score vs Validation score
train_acc = rf.score(X_train, y_train)
val_acc = rf.score(X_val, y_val)
print("\n===== TRAIN vs VALIDATION (overfitting check) =====")
print(f"Train Accuracy      : {train_acc:.4f}")
print(f"Validation Accuracy : {val_acc:.4f}")
print(f"Gap (Train - Val)   : {train_acc - val_acc:.4f}")

# Evaluate on the VALIDATION set (never used for training)
y_pred = rf.predict(X_val)
y_prob = rf.predict_proba(X_val)[:, 1]

# Print evaluation metrics
print("\n===== RANDOM FOREST RESULTS (on Validation set) =====")
print(f"Accuracy  : {accuracy_score(y_val, y_pred):.4f}")
print(f"Precision : {precision_score(y_val, y_pred):.4f}")
print(f"Recall    : {recall_score(y_val, y_pred):.4f}")
print(f"F1 Score  : {f1_score(y_val, y_pred):.4f}")
print(f"ROC-AUC   : {roc_auc_score(y_val, y_prob):.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_val, y_pred))

print("\nClassification Report:")
print(classification_report(y_val, y_pred,
      target_names=["Not Churned", "Churned"]))

# Feature importance chart
feat_imp = pd.Series(rf.feature_importances_,
                      index=X.columns).sort_values(ascending=True)
plt.figure(figsize=(10, 6))
feat_imp.plot.barh()
plt.title("Random Forest - Feature Importance")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/rf_feature_importance.png", dpi=150)

# Save model
with open(f"{OUTPUT_DIR}/random_forest_model.pkl", "wb") as f:
    pickle.dump(rf, f)

print(f"\nModel saved to: {OUTPUT_DIR}/random_forest_model.pkl")
