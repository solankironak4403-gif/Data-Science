"""
Script to generate and save SHAP and LIME explanation figures for the MCA Project Report.
Outputs:
1. reports/figures/shap_summary_bar.png (Global feature importance)
2. reports/figures/shap_waterfall_benign.png (Local SHAP waterfall for benign flow)
3. reports/figures/shap_waterfall_attack.png (Local SHAP waterfall for attack flow)
4. reports/figures/lime_explanation.png (Local LIME explanation bar plot)
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for generating images
import matplotlib.pyplot as plt
import shap
import lime
import lime.lime_tabular

# Ensure output directory exists
OUTPUT_DIR = os.path.join("reports", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading models and data for explanation plots...")
model = joblib.load("models/network_model.joblib")
feature_columns = joblib.load("models/feature_columns.joblib")
X_train = joblib.load("models/x_train_sample.joblib")
X_test = joblib.load("models/x_test_sample.joblib")
y_test = joblib.load("models/y_test.joblib")

if not isinstance(X_test, pd.DataFrame):
    X_test = pd.DataFrame(X_test, columns=feature_columns)
if not isinstance(X_train, pd.DataFrame):
    X_train = pd.DataFrame(X_train, columns=feature_columns)

y_test_arr = np.asarray(y_test).ravel()
benign_idx = np.where(y_test_arr == 0)[0][0]
attack_idx = np.where(y_test_arr == 1)[0][0]

print("Initializing SHAP TreeExplainer...")
explainer = shap.TreeExplainer(model)

# 1. Generate Global SHAP Summary Bar Plot (Top 15 features across 100 test samples)
print("\n[1/4] Generating Global SHAP Summary Bar Plot...")
shap_values_sample = explainer(X_test.iloc[:100])

plt.figure(figsize=(10, 6))
# For binary classification, shap_values_sample[:, :, 1] corresponds to Attack class
shap.plots.bar(shap_values_sample[:, :, 1], max_display=15, show=False)
plt.title("Global SHAP Feature Importance (CIC-IDS2017)", fontsize=13, pad=15)
plt.tight_layout()
shap_bar_path = os.path.join(OUTPUT_DIR, "shap_summary_bar.png")
plt.savefig(shap_bar_path, dpi=300)
plt.close()
print(f" -> Saved: {shap_bar_path}")

# 2. Local SHAP Waterfall Plot for Benign Flow
print("\n[2/4] Generating Local SHAP Waterfall Plot (Benign Flow)...")
shap_benign = explainer(X_test.iloc[[benign_idx]])
plt.figure(figsize=(10, 6))
shap.plots.waterfall(shap_benign[0, :, 1], max_display=10, show=False)
plt.title(f"SHAP Waterfall Explanation: Flow #{benign_idx} (True: BENIGN)", fontsize=13, pad=15)
plt.tight_layout()
waterfall_benign_path = os.path.join(OUTPUT_DIR, "shap_waterfall_benign.png")
plt.savefig(waterfall_benign_path, dpi=300)
plt.close()
print(f" -> Saved: {waterfall_benign_path}")

# 3. Local SHAP Waterfall Plot for Attack Flow
print("\n[3/4] Generating Local SHAP Waterfall Plot (Attack Flow)...")
shap_attack = explainer(X_test.iloc[[attack_idx]])
plt.figure(figsize=(10, 6))
shap.plots.waterfall(shap_attack[0, :, 1], max_display=10, show=False)
plt.title(f"SHAP Waterfall Explanation: Flow #{attack_idx} (True: ATTACK)", fontsize=13, pad=15)
plt.tight_layout()
waterfall_attack_path = os.path.join(OUTPUT_DIR, "shap_waterfall_attack.png")
plt.savefig(waterfall_attack_path, dpi=300)
plt.close()
print(f" -> Saved: {waterfall_attack_path}")

# 4. Local LIME Explanation Bar Plot
print("\n[4/4] Generating Local LIME Explanation Plot...")
lime_explainer = lime.lime_tabular.LimeTabularExplainer(
    training_data=X_train.values,
    feature_names=feature_columns,
    class_names=["Benign", "Attack"],
    mode="classification",
    random_state=42
)

def predict_fn(data):
    df = pd.DataFrame(data, columns=feature_columns)
    return model.predict_proba(df)

exp = lime_explainer.explain_instance(
    X_test.iloc[attack_idx].values,
    predict_fn,
    num_features=10,
    labels=[1]
)

fig = exp.as_pyplot_figure(label=1)
fig.set_size_inches(10, 6)
plt.title(f"LIME Local Explanation: Flow #{attack_idx} (ATTACK Decision Boundary)", fontsize=13, pad=15)
plt.tight_layout()
lime_plot_path = os.path.join(OUTPUT_DIR, "lime_explanation.png")
plt.savefig(lime_plot_path, dpi=300)
plt.close()
print(f" -> Saved: {lime_plot_path}")

print("\n" + "=" * 60)
print("  [COMPLETE] All 4 report figures successfully generated!  ")
print(f"  Directory: {os.path.abspath(OUTPUT_DIR)}")
print("=" * 60)

