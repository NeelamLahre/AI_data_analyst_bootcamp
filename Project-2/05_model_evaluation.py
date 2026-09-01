"""
Step 5 - Model Comparison & Evaluation
Loads both models, compares them side-by-side.
"""
import pandas as pd
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve,
    confusion_matrix, ConfusionMatrixDisplay,
)
from config import DATA_CLEANED, OUTPUT_DIR, TARGET, split_data

# Load data and the two saved models
df = pd.read_csv(DATA_CLEANED)
X = df.drop(columns=[TARGET])
y = df[TARGET]

# Same three-way split as Steps 3 & 4 (identical RANDOM_STATE -> identical rows).
# X_test/y_test have NOT been seen by either model until this exact moment -
# this is the one true, unbiased comparison.
X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)

with open(f"{OUTPUT_DIR}/decision_tree_model.pkl", "rb") as f:
    dt = pickle.load(f)
with open(f"{OUTPUT_DIR}/random_forest_model.pkl", "rb") as f:
    rf = pickle.load(f)

models = {"Decision Tree": dt, "Random Forest": rf}

# ---- Train vs Validation vs Test accuracy, for every model ----
# Seeing all three side by side makes overfitting/underfitting obvious:
#   Train >> Validation/Test  -> overfitting (memorized training data)
#   All three low             -> underfitting (model too simple / bad features)
#   All three close and high  -> good generalization
print("===== TRAIN / VALIDATION / TEST ACCURACY (overfitting check) =====")
for name, model in models.items():
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    test_acc = model.score(X_test, y_test)
    print(f"{name:15s} Train={train_acc:.4f}  Val={val_acc:.4f}  Test={test_acc:.4f}")
print()

# ---- Final comparison table, scored on the untouched TEST set ----
rows = []
for name, model in models.items():
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    # 5-fold cross-validation on the full dataset: an extra, independent
    # robustness check (trains/tests 5 different times, averages the F1 score)
    cv = cross_val_score(model, X, y, cv=5, scoring="f1")
    rows.append({
        "Model": name,
        "Accuracy": round(accuracy_score(y_test, y_pred), 4),
        "Precision": round(precision_score(y_test, y_pred), 4),
        "Recall": round(recall_score(y_test, y_pred), 4),
        "F1 Score": round(f1_score(y_test, y_pred), 4),
        "ROC-AUC": round(roc_auc_score(y_test, y_prob), 4),
        "CV F1 (mean)": round(cv.mean(), 4),
        "CV F1 (std)": round(cv.std(), 4),
    })

comparison = pd.DataFrame(rows)
print("===== FINAL COMPARISON (on Test set) =====")
print(comparison.to_string(index=False))
comparison.to_csv(f"{OUTPUT_DIR}/model_comparison.csv", index=False)

# ROC Curve - shows how well each model separates churners from non-churners
plt.figure(figsize=(8, 6))
for name, model in models.items():
    y_prob = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)
    plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")
plt.plot([0, 1], [0, 1], "k--", label="Random guessing")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve Comparison")
plt.legend()
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/roc_curve_comparison.png", dpi=150)

# Confusion Matrices side by side
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, (name, model) in zip(axes, models.items()):
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    ConfusionMatrixDisplay(cm,
        display_labels=["Not Churned", "Churned"]).plot(ax=ax)
    ax.set_title(name)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/confusion_matrices.png", dpi=150)

print("\nModel evaluation complete. See outputs/ for charts and model_comparison.csv")
