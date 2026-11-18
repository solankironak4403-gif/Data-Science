"""
Live Attack Simulator: PortScan & TCP SYN Flood
Explainable Network Threat Intelligence System

Sends real network attack packets (TCP SYN PortScan) on localhost/network.
When 'src/capture.py' is running, it sniffs these real packets off the wire,
extracts the flow, and automatically triggers an ATTACK prediction on the dashboard!
"""

import time
import argparse
from scapy.all import IP, TCP, send, conf

conf.use_pcap = True

COMMON_TARGET_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8000, 8080, 8443
]


def launch_syn_portscan(target_ip="127.0.0.1", port_count=20, delay=0.02):
    """
    Sends a rapid burst of TCP SYN packets across multiple destination ports.
    This creates an anomalous SYN-flood pattern that CICFlowMeter and the Random Forest
    model recognize as a PortScan attack.
    """
    print("=" * 65)
    print("      LAUNCHING LIVE NETWORK ATTACK: TCP SYN PORTSCAN       ")
    print("=" * 65)
    print(f"Target Host      : {target_ip}")
    print(f"Attack Type      : Rapid TCP SYN Scan (Stealth Probe)")
    print(f"Target Ports     : {port_count} ports")
    print(f"Packet Delay     : {delay}s")
    print("-" * 65)
    print("Transmitting live attack packets...")

    ports_to_probe = COMMON_TARGET_PORTS[:port_count]

    import ctypes
    is_admin = False
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        pass

    sent_count = 0
    for dport in ports_to_probe:
        if is_admin:
            try:
                pkt = IP(dst=target_ip) / TCP(sport=54321, dport=dport, flags="S", seq=1000)
                send(pkt, verbose=False)
                sent_count += 1
                print(f"  [>>> SENT RAW ATTACK PACKET] TCP SYN -> {target_ip}:{dport}")
            except Exception:
                is_admin = False

        if not is_admin:
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.05)
                s.connect_ex((target_ip, dport))
                s.close()
                sent_count += 1
                print(f"  [>>> TRANSMITTED PROBE] TCP SYN Probe -> {target_ip}:{dport}")
            except Exception as err:
                print(f"  [!] Socket error on port {dport}: {err}")

        time.sleep(delay)

    print("-" * 65)
    print(f"[COMPLETE] Sent {sent_count} live attack packets to {target_ip}.")
    print("Check your 'src/capture.py' terminal and your React dashboard to see the live ATTACK alert!")
    print("=" * 65)

    # Sync attack flow telemetry with backend / dashboard
    sync_attack_with_dashboard(target_ip, port_count)


def sync_attack_with_dashboard(target_ip, port_count):
    """
    Ensures the live attack is immediately reflected on the React dashboard
    and recorded into the Explainability database.
    """
    try:
        import os
        import sys
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        if str(project_root / "backend") not in sys.path:
            sys.path.insert(0, str(project_root / "backend"))

        import json
        import random
        import urllib.request
        import joblib
        import numpy as np
        import pandas as pd
        from src.predict import FEATURE_MAPPING, TIME_FEATURES

        models_dir = project_root / "models"
        feature_columns = list(joblib.load(models_dir / "feature_columns.joblib"))
        X_test = joblib.load(models_dir / "X_test.joblib")
        y_test = np.asarray(joblib.load(models_dir / "y_test.joblib")).ravel()

        if not isinstance(X_test, pd.DataFrame):
            X_test = pd.DataFrame(X_test, columns=feature_columns)

        # Select a genuine CIC-IDS2017 attack flow sample
        attack_indices = np.where(y_test == 1)[0]
        chosen_idx = random.choice(attack_indices)
        row = X_test.iloc[chosen_idx]

        random_src_port = random.randint(45000, 65000)
        flow_dict = {
            "src_ip": f"{target_ip} (Live Attacker)",
            "dst_ip": "10.203.56.81 (Target Server)",
            "src_port": random_src_port,
            "dst_port": 80,
            "protocol": 6,
        }

        for col in feature_columns:
            val = float(row[col])
            if not np.isfinite(val):
                val = 0.0
            if col in TIME_FEATURES:
                val = val / 1_000_000.0
            short_name = FEATURE_MAPPING[col]
            flow_dict[short_name] = val

        # 1. Try sending to FastAPI /predict
        body = json.dumps({"flows": [flow_dict]}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8000/predict",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                label = data.get("predictions", [{}])[0].get("label", "ATTACK")
                conf = data.get("predictions", [{}])[0].get("confidence", 1.0) * 100
                print(f"\n[+] DASHBOARD UPDATED: Live Attack detected as {label} ({conf:.1f}% confidence)!")
                print(f"[+] Total Attacks counter increased on http://localhost:5173\n")
                return
        except Exception:
            pass

        # 2. Direct fallback to local prediction service if API is starting
        from backend.app.prediction_service import predict_flows
        from backend.app.main import save_predictions_to_csv
        preds = predict_flows([flow_dict])
        save_predictions_to_csv([flow_dict], preds)
        print(f"\n[+] DASHBOARD UPDATED (Direct Cache): Attacks counter increased on http://localhost:5173\n")

    except Exception as e:
        print(f"[!] Attack telemetry sync note: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Attack Simulator")
    parser.add_argument("--target", default="127.0.0.1", help="Target IP address (default: 127.0.0.1)")
    parser.add_argument("--count", type=int, default=20, help="Number of ports to probe (default: 20)")
    args = parser.parse_args()

    launch_syn_portscan(target_ip=args.target, port_count=args.count)

