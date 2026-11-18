"""
Phase 8: Live Attack Prediction Module
Explainable Network Threat Intelligence System

This script loads the trained Random Forest model and feature columns,
processes live extracted flows from CICFlowMeter, validates and aligns features,
and produces predictions with uncertainty scores and confidence flags.
"""

import os
import joblib
import numpy as np
import pandas as pd


# 1. Feature Mapping: maps training 78 features to live CICFlowMeter columns
FEATURE_MAPPING = {
    "Destination Port": "dst_port",
    "Flow Duration": "flow_duration",
    "Total Fwd Packets": "tot_fwd_pkts",
    "Total Backward Packets": "tot_bwd_pkts",
    "Total Length of Fwd Packets": "totlen_fwd_pkts",
    "Total Length of Bwd Packets": "totlen_bwd_pkts",
    "Fwd Packet Length Max": "fwd_pkt_len_max",
    "Fwd Packet Length Min": "fwd_pkt_len_min",
    "Fwd Packet Length Mean": "fwd_pkt_len_mean",
    "Fwd Packet Length Std": "fwd_pkt_len_std",
    "Bwd Packet Length Max": "bwd_pkt_len_max",
    "Bwd Packet Length Min": "bwd_pkt_len_min",
    "Bwd Packet Length Mean": "bwd_pkt_len_mean",
    "Bwd Packet Length Std": "bwd_pkt_len_std",
    "Flow Bytes/s": "flow_byts_s",
    "Flow Packets/s": "flow_pkts_s",
    "Flow IAT Mean": "flow_iat_mean",
    "Flow IAT Std": "flow_iat_std",
    "Flow IAT Max": "flow_iat_max",
    "Flow IAT Min": "flow_iat_min",
    "Fwd IAT Total": "fwd_iat_tot",
    "Fwd IAT Mean": "fwd_iat_mean",
    "Fwd IAT Std": "fwd_iat_std",
    "Fwd IAT Max": "fwd_iat_max",
    "Fwd IAT Min": "fwd_iat_min",
    "Bwd IAT Total": "bwd_iat_tot",
    "Bwd IAT Mean": "bwd_iat_mean",
    "Bwd IAT Std": "bwd_iat_std",
    "Bwd IAT Max": "bwd_iat_max",
    "Bwd IAT Min": "bwd_iat_min",
    "Fwd PSH Flags": "fwd_psh_flags",
    "Bwd PSH Flags": "bwd_psh_flags",
    "Fwd URG Flags": "fwd_urg_flags",
    "Bwd URG Flags": "bwd_urg_flags",
    "Fwd Header Length": "fwd_header_len",
    "Bwd Header Length": "bwd_header_len",
    "Fwd Packets/s": "fwd_pkts_s",
    "Bwd Packets/s": "bwd_pkts_s",
    "Min Packet Length": "pkt_len_min",
    "Max Packet Length": "pkt_len_max",
    "Packet Length Mean": "pkt_len_mean",
    "Packet Length Std": "pkt_len_std",
    "Packet Length Variance": "pkt_len_var",
    "FIN Flag Count": "fin_flag_cnt",
    "SYN Flag Count": "syn_flag_cnt",
    "RST Flag Count": "rst_flag_cnt",
    "PSH Flag Count": "psh_flag_cnt",
    "ACK Flag Count": "ack_flag_cnt",
    "URG Flag Count": "urg_flag_cnt",
    "CWE Flag Count": "cwr_flag_count",
    "ECE Flag Count": "ece_flag_cnt",
    "Down/Up Ratio": "down_up_ratio",
    "Average Packet Size": "pkt_size_avg",
    "Avg Fwd Segment Size": "fwd_seg_size_avg",
    "Avg Bwd Segment Size": "bwd_seg_size_avg",
    "Fwd Header Length.1": "fwd_header_len",
    "Fwd Avg Bytes/Bulk": "fwd_byts_b_avg",
    "Fwd Avg Packets/Bulk": "fwd_pkts_b_avg",
    "Fwd Avg Bulk Rate": "fwd_blk_rate_avg",
    "Bwd Avg Bytes/Bulk": "bwd_byts_b_avg",
    "Bwd Avg Packets/Bulk": "bwd_pkts_b_avg",
    "Bwd Avg Bulk Rate": "bwd_blk_rate_avg",
    "Subflow Fwd Packets": "subflow_fwd_pkts",
    "Subflow Fwd Bytes": "subflow_fwd_byts",
    "Subflow Bwd Packets": "subflow_bwd_pkts",
    "Subflow Bwd Bytes": "subflow_bwd_byts",
    "Init_Win_bytes_forward": "init_fwd_win_byts",
    "Init_Win_bytes_backward": "init_bwd_win_byts",
    "act_data_pkt_fwd": "fwd_act_data_pkts",
    "min_seg_size_forward": "fwd_seg_size_min",
    "Active Mean": "active_mean",
    "Active Std": "active_std",
    "Active Max": "active_max",
    "Active Min": "active_min",
    "Idle Mean": "idle_mean",
    "Idle Std": "idle_std",
    "Idle Max": "idle_max",
    "Idle Min": "idle_min"
}

# Features that use microsecond time units in CIC-IDS2017
TIME_FEATURES = [
    "Flow Duration", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Total", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min"
]


def _resolve_project_file(rel_path: str) -> str:
    """Resolve file path whether called from project root or backend subfolder."""
    if os.path.exists(rel_path):
        return rel_path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidate = os.path.join(project_root, rel_path)
    if os.path.exists(candidate):
        return candidate
    candidate2 = os.path.join("..", rel_path)
    if os.path.exists(candidate2):
        return candidate2
    return rel_path


def load_model_and_features(
    model_path: str = "models/network_model.joblib",
    features_path: str = "models/feature_columns.joblib"
):
    """Load the pre-trained Random Forest model and the exact 78 feature column names."""
    model_path = _resolve_project_file(model_path)
    features_path = _resolve_project_file(features_path)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Feature columns file not found at: {features_path}")

    model = joblib.load(model_path)
    feature_columns = joblib.load(features_path)
    return model, feature_columns


def prepare_live_features(
    live_df: pd.DataFrame,
    feature_columns: list,
    convert_seconds_to_microseconds: bool = True
) -> pd.DataFrame:
    """
    Transform and validate raw live flows into model-compatible features:
    1. Selects and renames columns according to FEATURE_MAPPING and feature_columns order.
    2. Adjusts time feature units if extracted in seconds (CIC-IDS2017 expects microseconds).
    3. Handles infinite values (resulting from zero-duration flow rate divisions).
    4. Handles missing (NaN) values cleanly.
    5. Clips negative values to 0 where values must be non-negative.
    """
    # Verify all required mapped columns exist in input
    missing_cols = [
        col for col in feature_columns
        if col not in FEATURE_MAPPING or FEATURE_MAPPING[col] not in live_df.columns
    ]
    if missing_cols:
        raise ValueError(f"Input data is missing mapped columns for: {missing_cols}")

    # Extract features in the exact expected order
    mapped_col_names = [FEATURE_MAPPING[col] for col in feature_columns]
    X_live = live_df[mapped_col_names].copy()
    X_live.columns = feature_columns

    # Time unit conversion:
    # Python cicflowmeter stores duration and IAT in fractional seconds (e.g. 0.149s),
    # while CIC-IDS2017 training data uses microseconds (e.g. 149000us).
    if convert_seconds_to_microseconds:
        for col in TIME_FEATURES:
            if col in X_live.columns:
                # If values are small (median < 1000), they are in seconds, so convert to microseconds
                if X_live[col].dropna().median() < 1000:
                    X_live[col] = X_live[col] * 1_000_000.0

    # Replace infinite values (from division by zero-duration flows) with 0.0
    X_live = X_live.replace([np.inf, -np.inf], 0.0)

    # Impute any missing (NaN) values with 0.0
    X_live = X_live.fillna(0.0)

    # Convert all columns to numeric float64
    X_live = X_live.astype(np.float64)

    # Clip any accidental negative values (e.g. invalid header or counter offsets) to 0
    X_live = X_live.clip(lower=0.0)

    return X_live


def predict_live_flows(
    model_path: str = "models/network_model.joblib",
    features_path: str = "models/feature_columns.joblib",
    flows_path: str = "data/processed/live_flows.csv",
    output_path: str = "data/processed/live_prediction_results.csv",
    confidence_threshold: float = 0.70
) -> pd.DataFrame:
    """
    Execute Phase 8 live traffic attack prediction:
    1. Loads model and feature definitions.
    2. Loads live network flows CSV.
    3. Prepares and validates the 78 features.
    4. Performs binary prediction (0: BENIGN, 1: ATTACK).
    5. Computes prediction probability and uncertainty score.
    6. Identifies predictions needing manual review (Confidence < threshold).
    7. Returns an enriched summary DataFrame.
    """
    print("=" * 60)
    print("  PHASE 8: LIVE ATTACK PREDICTION & UNCERTAINTY ANALYSIS  ")
    print("=" * 60)

    # 1. Load model and features
    print("\n[Step 1] Loading model and feature schema...")
    model, feature_columns = load_model_and_features(model_path, features_path)
    print(f" -> Model Loaded: {type(model).__name__}")
    print(f" -> Expected Features: {len(feature_columns)}")

    # 2. Load live traffic CSV
    print(f"\n[Step 2] Loading live flows from: {flows_path}...")
    if not os.path.exists(flows_path):
        raise FileNotFoundError(f"Live flows CSV not found at: {flows_path}")
    live_df = pd.read_csv(flows_path)
    print(f" -> Live flows loaded: {len(live_df)} records")

    # 3. Prepare and validate features
    print("\n[Step 3] Preprocessing and validating 78 flow features...")
    X_live = prepare_live_features(live_df, feature_columns)
    print(f" -> Prepared feature matrix shape: {X_live.shape}")
    print(f" -> Remaining NaNs: {X_live.isnull().sum().sum()}")
    print(f" -> Remaining Infs: {np.isinf(X_live.values).sum()}")

    # 4. Model Prediction
    print("\n[Step 4] Running Random Forest classifier...")
    predictions = model.predict(X_live)
    probabilities = model.predict_proba(X_live)

    # Probability of class 0 (Benign) and class 1 (Attack)
    # Binary classification labels: 0 = BENIGN, 1 = ATTACK
    prob_benign = probabilities[:, 0]
    prob_attack = probabilities[:, 1]

    # 5. Uncertainty & Confidence calculation
    # Confidence is max predicted probability; Uncertainty is (1 - Confidence)
    confidence = np.max(probabilities, axis=1)
    uncertainty = 1.0 - confidence

    # 6. Status determination (Confidence Threshold: 0.70)
    status = [
        "High Confidence" if conf >= confidence_threshold else "Low Confidence (Review Required)"
        for conf in confidence
    ]

    label_map = {0: "BENIGN", 1: "ATTACK"}
    prediction_labels = [label_map[p] for p in predictions]

    # Protocol mapping
    proto_map = {6: "TCP", 17: "UDP"}
    protocols = [
        proto_map.get(p, str(p)) if p in proto_map else str(p)
        for p in live_df["protocol"]
    ] if "protocol" in live_df.columns else ["Unknown"] * len(live_df)

    # 7. Construct structured results DataFrame
    results_df = pd.DataFrame({
        "flow_id": range(1, len(live_df) + 1),
        "src_ip": live_df["src_ip"] if "src_ip" in live_df.columns else "N/A",
        "dst_ip": live_df["dst_ip"] if "dst_ip" in live_df.columns else "N/A",
        "src_port": live_df["src_port"] if "src_port" in live_df.columns else 0,
        "dst_port": live_df["dst_port"] if "dst_port" in live_df.columns else 0,
        "protocol": protocols,
        "prediction": predictions,
        "label": prediction_labels,
        "prob_benign": np.round(prob_benign, 4),
        "prob_attack": np.round(prob_attack, 4),
        "confidence": np.round(confidence, 4),
        "uncertainty": np.round(uncertainty, 4),
        "status": status
    })

    # Display clear summary
    print("\n[Step 5] Prediction Results Summary:")
    print("-" * 60)
    print(f"Total Flows Analyzed: {len(results_df)}")
    print(f"Benign Flows Detected: {(predictions == 0).sum()}")
    print(f"Attack Flows Detected: {(predictions == 1).sum()}")
    print(f"High Confidence Flows: {status.count('High Confidence')}")
    print(f"Low Confidence Flows : {len(status) - status.count('High Confidence')}")
    print("-" * 60)

    # Display table preview
    display_cols = [
        "flow_id", "src_ip", "dst_ip", "protocol", "label",
        "confidence", "uncertainty", "status"
    ]
    print(results_df[display_cols].to_string(index=False))

    # Save results to CSV if output_path is provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        results_df.to_csv(output_path, index=False)
        print(f"\n[Saved] Detailed predictions saved to: {output_path}")

    return results_df


if __name__ == "__main__":
    results = predict_live_flows()
