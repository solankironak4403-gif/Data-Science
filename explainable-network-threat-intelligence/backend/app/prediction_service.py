
import pandas as pd
import numpy as np

from app.model import model, feature_columns


# Map CICFlowMeter columns to model training features
feature_mapping = {
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


# Time-related features
time_features = [
    "Flow Duration",
    "Flow IAT Mean", "Flow IAT Std",
    "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Total", "Fwd IAT Mean",
    "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Total", "Bwd IAT Mean",
    "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Active Mean", "Active Std",
    "Active Max", "Active Min",
    "Idle Mean", "Idle Std",
    "Idle Max", "Idle Min"
]


def predict_flows(flows):

    # Convert incoming flows into DataFrame
    live_flows = pd.DataFrame(flows)

    # Check required input columns
    required_columns = set(feature_mapping.values())

    missing_columns = required_columns - set(live_flows.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # Select features in the exact training order
    live_features = live_flows[
        [feature_mapping[col] for col in feature_columns]
    ].copy()

    # Rename columns to model feature names
    live_features.columns = feature_columns

    # Convert values into numeric format
    live_features = live_features.apply(
        pd.to_numeric, errors="coerce"
    )

    # Convert seconds to microseconds when needed
    X_live_clean = live_features.copy()

    for col in time_features:
        if col in X_live_clean.columns:
            if X_live_clean[col].dropna().median() < 1000:
                X_live_clean[col] = (
                    X_live_clean[col] * 1_000_000.0
                )

    # Clean missing and infinite values
    X_live_clean = X_live_clean.replace(
        [np.inf, -np.inf], 0.0
    ).fillna(0.0).clip(lower=0.0)

    # ML predictions
    predictions = model.predict(X_live_clean)
    probabilities = model.predict_proba(X_live_clean)

    # Calculate confidence and uncertainty
    confidence = np.max(probabilities, axis=1)
    uncertainty = 1.0 - confidence

    confidence_threshold = 0.70

    label_map = {
        0: "BENIGN",
        1: "ATTACK"
    }

    results = []

    for i in range(len(predictions)):

        prediction = int(predictions[i])
        conf = float(confidence[i])
        uncert = float(uncertainty[i])

        results.append({
            "flow_id": i + 1,
            "prediction": prediction,
            "label": label_map[prediction],
            "confidence": round(conf, 4),
            "uncertainty": round(uncert, 4),
            "status": (
                "High Confidence"
                if conf >= confidence_threshold
                else "Low Confidence (Manual Review)"
            )
        })

    return results
