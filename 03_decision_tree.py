"""
Step 3 - Decision Tree Classifier
Trains a Decision Tree on the cleaned data, saves the model.
"""
import pandas as pd
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score,
)
from config import DATA_CLEANED, OUTPUT_DIR, TARGET, RANDOM_STATE, split_data

# Load cleaned data
df = pd.read_csv(DATA_CLEANED)
X = df.drop(columns=[TARGET])  # Features (input) - everything except Churn
y = df[TARGET]                  # Target (output) - the Churn column

# Three-way split: Train (60%) / Validation (20%) / Test (20%)
# Test is intentionally NOT touched in this file - it's saved for Step 5.
X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
print(f"Train: {X_train.shape}, Validation: {X_val.shape}, Test: {X_test.shape}")

# Create and train the Decision Tree
dt = DecisionTreeClassifier(
    max_depth=8, min_samples_split=20, random_state=RANDOM_STATE
)
dt.fit(X_train, y_train)  # This is where the model LEARNS, using ONLY the training set

# Check for overfitting/underfitting: compare score on data it learned from
# (Train) vs data it did NOT learn from (Validation).
train_acc = dt.score(X_train, y_train)
val_acc = dt.score(X_val, y_val)
print("\n===== TRAIN vs VALIDATION (overfitting check) =====")
print(f"Train Accuracy      : {train_acc:.4f}")
print(f"Validation Accuracy : {val_acc:.4f}")
print(f"Gap (Train - Val)   : {train_acc - val_acc:.4f}")
print("A big gap here (e.g. Train much higher than Validation) means overfitting.")

# Evaluate on the VALIDATION set (never used for training)
y_pred = dt.predict(X_val)
y_prob = dt.predict_proba(X_val)[:, 1]  # probability of churn

# Print evaluation metrics
print("\n===== DECISION TREE RESULTS (on Validation set) =====")
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

# Feature importance chart - which columns mattered most to the model?
feat_imp = pd.Series(dt.feature_importances_,
                      index=X.columns).sort_values(ascending=True)
plt.figure(figsize=(10, 6))
feat_imp.plot.barh()
plt.title("Decision Tree - Feature Importance")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/dt_feature_importance.png", dpi=150)

# Visualize the tree itself (top 4 levels, otherwise it's unreadable)
plt.figure(figsize=(24, 10))
plot_tree(dt, max_depth=4, feature_names=X.columns,
          class_names=["No", "Yes"], filled=True, rounded=True, fontsize=8)
plt.title("Decision Tree (top 4 levels)")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/dt_tree_plot.png", dpi=150)

# Save the trained model to disk so later steps can reuse it
with open(f"{OUTPUT_DIR}/decision_tree_model.pkl", "wb") as f:
    pickle.dump(dt, f)

print(f"\nModel saved to: {OUTPUT_DIR}/decision_tree_model.pkl")
