"""
Test script for Phase 13 Explainability (SHAP & LIME)
"""

import sys
import os
import joblib
import pandas as pd
import numpy as np

# Ensure backend and project root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.explanation_service import generate_flow_explanation

def test_explainability():
    print("=" * 60)
    print("  PHASE 13 EXPLAINABILITY TEST (SHAP & LIME)  ")
    print("=" * 60)

    # Load real live flows from CSV
    flows_path = os.path.join("..", "data", "processed", "live_flows.csv")
    if not os.path.exists(flows_path):
        flows_path = os.path.join("data", "processed", "live_flows.csv")

    flows_df = pd.read_csv(flows_path)
    test_flow = flows_df.iloc[0].to_dict()

    print(f"Target Flow: Source IP={test_flow.get('src_ip')} -> Dst IP={test_flow.get('dst_ip')} Port={test_flow.get('dst_port')}")

    # 1. Test SHAP Explanation
    print("\n[1] Testing SHAP TreeExplainer (Top 10 Features)...")
    shap_exp = generate_flow_explanation(test_flow, method="shap", top_n=10)

    print(f"  -> Prediction: {shap_exp['label']}")
    print(f"  -> Confidence: {shap_exp['confidence'] * 100:.2f}%")
    print(f"  -> Attack Probability: {shap_exp['attack_probability'] * 100:.2f}%")
    print(f"  -> Base Value: {shap_exp['base_value']}")
    print("  -> Top SHAP Features:")
    for i, item in enumerate(shap_exp["top_features"], 1):
        print(f"     {i:2d}. {item['feature']:<30} = {item['value']:<10} (SHAP: {item['importance']:+.4f}) -> {item['effect']}")

    assert len(shap_exp["top_features"]) == 10
    assert "label" in shap_exp
    assert "attack_probability" in shap_exp

    # 2. Test LIME Explanation
    print("\n[2] Testing LIME TabularExplainer (Top 10 Features)...")
    lime_exp = generate_flow_explanation(test_flow, method="lime", top_n=10)

    print(f"  -> Prediction: {lime_exp['label']}")
    print(f"  -> Confidence: {lime_exp['confidence'] * 100:.2f}%")
    print(f"  -> Attack Probability: {lime_exp['attack_probability'] * 100:.2f}%")
    print("  -> Top LIME Features:")
    for i, item in enumerate(lime_exp["top_features"], 1):
        print(f"     {i:2d}. {item['feature']:<40} (Weight: {item['importance']:+.4f}) -> {item['effect']}")

    assert len(lime_exp["top_features"]) == 10
    assert "label" in lime_exp

    print("\n" + "=" * 60)
    print("  [PASSED] Both SHAP and LIME backend services are verified!  ")
    print("=" * 60)

if __name__ == "__main__":
    test_explainability()

