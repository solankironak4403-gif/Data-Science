"""
Phase 13: Explainable AI (XAI) Module - SHAP & LIME
Explainable Network Threat Intelligence System

Provides model explainability using SHAP (TreeExplainer) and LIME (LimeTabularExplainer)
to identify and rank the top features driving individual attack and benign predictions.
"""

import os
import sys
import tempfile

# Ensure matplotlib uses a writable temporary directory to avoid lock delays
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import joblib
import numpy as np
import pandas as pd
import shap
import lime
import lime.lime_tabular

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.predict import (
    FEATURE_MAPPING,
    TIME_FEATURES,
    prepare_live_features,
    load_model_and_features,
    _resolve_project_file
)

# Global cached explainers for high API performance
_MODEL = None
_FEATURE_COLUMNS = None
_X_TRAIN_SAMPLE = None
_SHAP_EXPLAINER = None
_LIME_EXPLAINER = None


def get_explainers(
    model_path: str = "models/network_model.joblib",
    features_path: str = "models/feature_columns.joblib",
    train_sample_path: str = "models/x_train_sample.joblib"
):
    """
    Lazy-load and cache the Random Forest model, feature schema,
    background training sample, SHAP TreeExplainer, and LIME TabularExplainer.
    """
    global _MODEL, _FEATURE_COLUMNS, _X_TRAIN_SAMPLE, _SHAP_EXPLAINER, _LIME_EXPLAINER

    if _SHAP_EXPLAINER is not None and _LIME_EXPLAINER is not None:
        return _MODEL, _FEATURE_COLUMNS, _SHAP_EXPLAINER, _LIME_EXPLAINER

    # 1. Load model and feature columns
    _MODEL, _FEATURE_COLUMNS = load_model_and_features(model_path, features_path)

    # 2. Load background training sample for explainers
    resolved_sample_path = _resolve_project_file(train_sample_path)
    if not os.path.exists(resolved_sample_path):
        raise FileNotFoundError(f"Training sample not found at: {train_sample_path}")
    _X_TRAIN_SAMPLE = joblib.load(resolved_sample_path)
    if isinstance(_X_TRAIN_SAMPLE, pd.DataFrame):
        _X_TRAIN_SAMPLE = _X_TRAIN_SAMPLE[_FEATURE_COLUMNS]

    # 3. Initialize SHAP TreeExplainer (optimized for tree ensembles like Random Forest)
    _SHAP_EXPLAINER = shap.TreeExplainer(_MODEL)

    # 4. Initialize LIME TabularExplainer
    _LIME_EXPLAINER = lime.lime_tabular.LimeTabularExplainer(
        training_data=_X_TRAIN_SAMPLE.values,
        feature_names=_FEATURE_COLUMNS,
        class_names=["Benign", "Attack"],
        mode="classification",
        random_state=42
    )

    return _MODEL, _FEATURE_COLUMNS, _SHAP_EXPLAINER, _LIME_EXPLAINER


def prepare_single_flow(flow_dict_or_df, feature_columns):
    """
    Ensure input flow is converted into a 1-row DataFrame matching the 78 training features.
    Accepts raw CICFlowMeter dictionary, live flow dictionary, or existing feature DataFrame.
    """
    if isinstance(flow_dict_or_df, dict):
        df = pd.DataFrame([flow_dict_or_df])
    elif isinstance(flow_dict_or_df, pd.Series):
        df = pd.DataFrame([flow_dict_or_df])
    else:
        df = flow_dict_or_df.copy()

    # If columns match live CICFlowMeter output, map and clean them
    if any(col in df.columns for col in FEATURE_MAPPING.values()):
        return prepare_live_features(df, feature_columns)

    # If already using the 78 model feature names
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        # Fill missing with 0.0
        for c in missing:
            df[c] = 0.0

    df = df[feature_columns].copy()
    df = df.replace([np.inf, -np.inf], 0.0).fillna(0.0).clip(lower=0.0)
    return df.astype(np.float64)


def explain_flow_shap(flow_data, top_n: int = 10):
    """
    Generate SHAP local explanation for a single network flow.
    Identifies the top_n features contributing towards ATTACK (positive) or BENIGN (negative).
    """
    model, feature_columns, shap_explainer, _ = get_explainers()
    X_flow = prepare_single_flow(flow_data, feature_columns)

    # Model prediction and probabilities
    pred = int(model.predict(X_flow)[0])
    probs = model.predict_proba(X_flow)[0]
    confidence = float(np.max(probs))
    label = "ATTACK" if pred == 1 else "BENIGN"

    # Compute SHAP values
    shap_res = shap_explainer(X_flow)

    # TreeExplainer returns shape (1, 78, 2) for binary classification
    if len(shap_res.values.shape) == 3:
        # Focus on class 1 (Attack probability impact)
        shap_vals = shap_res.values[0, :, 1]
        base_val = float(shap_res.base_values[0, 1])
    else:
        shap_vals = shap_res.values[0]
        base_val = float(shap_res.base_values[0])

    feature_values = X_flow.iloc[0].values

    # Rank features by absolute SHAP magnitude
    indices = np.argsort(np.abs(shap_vals))[::-1][:top_n]

    top_features = []
    for idx in indices:
        feat_name = feature_columns[idx]
        val = float(feature_values[idx])
        importance = float(shap_vals[idx])
        effect = "Pushes toward ATTACK" if importance > 0 else "Pushes toward BENIGN"

        top_features.append({
            "feature": feat_name,
            "value": round(val, 4),
            "importance": round(importance, 4),
            "effect": effect
        })

    return {
        "method": "shap",
        "prediction": pred,
        "label": label,
        "confidence": round(confidence, 4),
        "attack_probability": round(float(probs[1]), 4),
        "benign_probability": round(float(probs[0]), 4),
        "base_value": round(base_val, 4),
        "top_features": top_features
    }


def explain_flow_lime(flow_data, top_n: int = 10):
    """
    Generate LIME local explanation for a single network flow.
    Fits a local linear surrogate model around the instance to explain the prediction.
    """
    model, feature_columns, _, lime_explainer = get_explainers()
    X_flow = prepare_single_flow(flow_data, feature_columns)

    # Model prediction
    pred = int(model.predict(X_flow)[0])
    probs = model.predict_proba(X_flow)[0]
    confidence = float(np.max(probs))
    label = "ATTACK" if pred == 1 else "BENIGN"

    # Prediction wrapper for LIME
    def predict_fn(data):
        df = pd.DataFrame(data, columns=feature_columns)
        return model.predict_proba(df)

    instance_values = X_flow.iloc[0].values
    exp = lime_explainer.explain_instance(
        instance_values,
        predict_fn,
        num_features=top_n,
        num_samples=1000,
        labels=[1]  # Explain Attack class
    )

    lime_list = exp.as_list(label=1)
    top_features = []
    for rule_str, weight in lime_list:
        effect = "Pushes toward ATTACK" if weight > 0 else "Pushes toward BENIGN"
        top_features.append({
            "feature": rule_str,
            "importance": round(float(weight), 4),
            "effect": effect
        })

    return {
        "method": "lime",
        "prediction": pred,
        "label": label,
        "confidence": round(confidence, 4),
        "attack_probability": round(float(probs[1]), 4),
        "benign_probability": round(float(probs[0]), 4),
        "top_features": top_features
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  Testing src/explain.py: SHAP and LIME Explanations  ")
    print("=" * 60)

    # Test with live flow from live_flows.csv
    flows_df = pd.read_csv("data/processed/live_flows.csv")
    first_flow = flows_df.iloc[0].to_dict()

    print("\n--- 1. Testing SHAP Explanation ---")
    shap_result = explain_flow_shap(first_flow, top_n=5)
    print(f"Prediction: {shap_result['label']} (Confidence: {shap_result['confidence']})")
    print("Top 5 SHAP Features:")
    for f in shap_result["top_features"]:
        print(f"  * {f['feature']}: importance={f['importance']} ({f['effect']})")

    print("\n--- 2. Testing LIME Explanation ---")
    lime_result = explain_flow_lime(first_flow, top_n=5)
    print(f"Prediction: {lime_result['label']} (Confidence: {lime_result['confidence']})")
    print("Top 5 LIME Features:")
    for f in lime_result["top_features"]:
        print(f"  * {f['feature']}: weight={f['importance']} ({f['effect']})")

    print("\n[SUCCESS] Both SHAP and LIME ran successfully!")
