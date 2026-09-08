import joblib
import shap
import lime.lime_tabular
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---- Load model and data ----
X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split.pkl')
model = joblib.load('outputs/xgboost_model.pkl')  # the nominal top performer from Step 9

# Sample for SHAP (running on the full 200K+ row test set would be slow)
X_sample = X_test.sample(2000, random_state=42)

# ---- Global feature importance (SHAP summary plot) ----
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_sample)

plt.figure(figsize=(12, 8))
shap.summary_plot(shap_values, X_sample, show=False)
plt.tight_layout()
plt.savefig('outputs/shap_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved outputs/shap_summary.png')

# ---- Explain one individual prediction ----
patient_idx = 0
row = X_sample.iloc[[patient_idx]]
prob = model.predict_proba(row)[0][1]
print(f'Predicted probability of Effective: {prob:.3f}')

shap.force_plot(
    explainer.expected_value, shap_values[patient_idx], row,
    matplotlib=True, show=False
)
plt.savefig('outputs/shap_force_patient0.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved outputs/shap_force_patient0.png')

# ---- LIME, for comparison ----
# Use a SMALL sample as LIME's reference set, not the full 811K-row X_train —
# LIME's constructor computes per-feature statistics over whatever it's given,
# and doing that over the full training set is what caused the earlier hang.
X_train_sample = X_train.sample(3000, random_state=42)

lime_explainer = lime.lime_tabular.LimeTabularExplainer(
    X_train_sample.values, feature_names=X_train.columns.tolist(),
    class_names=['Ineffective', 'Effective'], mode='classification'
)
explanation = lime_explainer.explain_instance(
    X_sample.iloc[0].values, model.predict_proba, num_features=10
)
print('LIME explanation for the same patient:')
for feature, weight in explanation.as_list():
    direction = 'Effective' if weight > 0 else 'Ineffective'
    print(f'  {feature}: {weight:+.4f} -> pushes toward {direction}')

fig = explanation.as_pyplot_figure()
fig.tight_layout()
fig.savefig('outputs/lime_explanation_patient0.png', dpi=150)
plt.close()
print('Saved outputs/lime_explanation_patient0.png')

print('\nStep 10 complete.')