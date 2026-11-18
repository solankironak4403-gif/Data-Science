"""
Simulate and Inject Real Attack Network Flows into the Threat Intelligence System
Explainable Network Threat Intelligence System
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
URL_PREDICT = "http://127.0.0.1:8000/predict"

sys.path.insert(0, str(ROOT_DIR))
from src.predict import FEATURE_MAPPING, TIME_FEATURES


def send_attack_flows(num_attacks: int = 3, num_benign: int = 1):
    print("=" * 65)
    print("  SIMULATING AND PREDICTING NETWORK ATTACKS (CIC-IDS2017)  ")
    print("=" * 65)

    feature_columns = list(joblib.load(MODELS_DIR / "feature_columns.joblib"))
    X_test = joblib.load(MODELS_DIR / "X_test.joblib")
    y_test = np.asarray(joblib.load(MODELS_DIR / "y_test.joblib")).ravel()

    if not isinstance(X_test, pd.DataFrame):
        X_test = pd.DataFrame(X_test, columns=feature_columns)

    # 1. Select genuine Attack and Benign flows from test dataset
    attack_indices = np.where(y_test == 1)[0][:num_attacks]
    benign_indices = np.where(y_test == 0)[0][:num_benign]
    selected_indices = list(attack_indices) + list(benign_indices)

    # Realistic simulation IPs and protocols
    attacker_ips = ["192.168.1.105 (Attacker)", "172.16.0.45 (Botnet)", "10.0.0.99 (Infiltrator)"]
    victim_ip = "192.168.1.1 (Server Target)"

    flows_payload = []
    flow_rows_for_csv = []

    for idx, sample_idx in enumerate(selected_indices):
        is_attack = sample_idx in attack_indices
        row = X_test.iloc[sample_idx]

        src_ip = attacker_ips[idx % len(attacker_ips)] if is_attack else "192.168.1.50 (User PC)"
        dst_ip = victim_ip
        src_port = 45000 + idx * 10
        dst_port = 80 if is_attack else 443
        protocol = 6  # TCP

        flow_dict = {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
        }

        # Map the 78 features to short CICFlowMeter column names
        for col in feature_columns:
            val = float(row[col])
            if not np.isfinite(val):
                val = 0.0
            # Scale seconds for the backend preprocessor
            if col in TIME_FEATURES:
                val = val / 1_000_000.0
            short_name = FEATURE_MAPPING[col]
            flow_dict[short_name] = val

        flows_payload.append(flow_dict)

    # 2. Send payload to FastAPI /predict (or fallback to prediction_service directly)
    print(f"\n[Step 1] Processing {len(flows_payload)} flows ({num_attacks} Attacks, {num_benign} Benign)...")
    result = None
    try:
        req_body = json.dumps({"flows": flows_payload}).encode("utf-8")
        req = urllib.request.Request(
            URL_PREDICT,
            data=req_body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Standalone fallback: predict directly via prediction_service
        from app.prediction_service import predict_flows
        preds = predict_flows(flows_payload)
        result = {"total_flows": len(preds), "predictions": preds}

    # 3. Print prediction results
    print("\n[Step 2] Model Predictions Received:")
    print("-" * 65)
    print(f"{'FLOW':<6} {'SOURCE IP':<26} {'LABEL':<10} {'CONFIDENCE':<12} {'STATUS'}")
    print("-" * 65)

    for i, (flow, pred) in enumerate(zip(flows_payload, result["predictions"]), 1):
        print(f"#{i:<5} {flow['src_ip']:<26} {pred['label']:<10} {pred['confidence']*100:>6.2f}%      {pred['status']}")

    # 4. Also update live flows CSV so the Explainability page lists the attack flow!
    live_csv_path = ROOT_DIR / "data" / "processed" / "live_flows.csv"
    preds_csv_path = ROOT_DIR / "data" / "processed" / "live_prediction_results.csv"

    if live_csv_path.exists():
        existing_live = pd.read_csv(live_csv_path)
        attack_rows = pd.DataFrame(flows_payload)
        updated_live = pd.concat([attack_rows, existing_live], ignore_index=True)
        updated_live.to_csv(live_csv_path, index=False)

    if preds_csv_path.exists():
        existing_preds = pd.read_csv(preds_csv_path)
        new_preds = []
        for i, (flow, pred) in enumerate(zip(flows_payload, result["predictions"]), 1):
            new_preds.append({
                "flow_id": i,
                "src_ip": flow["src_ip"],
                "dst_ip": flow["dst_ip"],
                "src_port": flow["src_port"],
                "dst_port": flow["dst_port"],
                "protocol": "TCP",
                "prediction": pred["prediction"],
                "label": pred["label"],
                "prob_benign": round(1.0 - pred["confidence"] if pred["prediction"] == 1 else pred["confidence"], 4),
                "prob_attack": round(pred["confidence"] if pred["prediction"] == 1 else 1.0 - pred["confidence"], 4),
                "confidence": round(pred["confidence"], 4),
                "uncertainty": round(pred["uncertainty"], 4),
                "status": pred["status"]
            })
        updated_preds = pd.concat([pd.DataFrame(new_preds), existing_preds], ignore_index=True)
        updated_preds["flow_id"] = range(1, len(updated_preds) + 1)
        updated_preds.to_csv(preds_csv_path, index=False)

    print("-" * 65)
    print("\n[SUCCESS] Attack flows have been predicted and injected!")
    print("Now open http://localhost:5173 and check:")
    print("  1. Dashboard: 'Attacks Detected' counter will increase!")
    print("  2. Attack Detection page: Active Threat Alert with Red Badges!")
    print("  3. Explainability page: Click the Attack flow to see RED SHAP bars!")
    print("=" * 65)


if __name__ == "__main__":
    send_attack_flows(num_attacks=3, num_benign=1)
