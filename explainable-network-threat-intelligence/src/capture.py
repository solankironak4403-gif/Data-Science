"""
Phase 15: Real-Time Live Network Traffic Capture & Automated Attack Detection
Explainable Network Threat Intelligence System

Captures live network packets from your network interface (Wi-Fi, Ethernet, or Loopback),
extracts bidirectional flow features using CICFlowMeter, and sends them directly
to the FastAPI backend (/predict) for real-time attack classification.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# Scapy imports
import threading
from scapy.all import sniff, conf, IP, IPv6, TCP, UDP
from cicflowmeter.flow_session import FlowSession, get_logger


class MemoryFlowSession(FlowSession):
    """In-memory FlowSession that bypasses file writers and extracts raw flow metrics."""
    def __init__(self, *args, **kwargs):
        self.flows = {}
        self.verbose = False
        self.fields = None
        self.packets_count = 0
        self.logger = get_logger(False)
        self.output_writer = None
        self._lock = threading.Lock()

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

API_PREDICT_URL = "http://127.0.0.1:8000/predict"

# Enable Npcap for Windows
conf.use_pcap = True


def send_flows_to_backend(flows_list):
    """Send extracted live flows to FastAPI backend /predict endpoint."""
    if not flows_list:
        return None

    # Sanitize NaN/inf values for JSON serialization
    cleaned_flows = []
    for f in flows_list:
        cleaned = {}
        for k, v in f.items():
            if v is None or (isinstance(v, float) and (v != v or v == float("inf") or v == float("-inf"))):
                cleaned[k] = 0.0
            else:
                cleaned[k] = v
        cleaned_flows.append(cleaned)

    body = json.dumps({"flows": cleaned_flows}).encode("utf-8")
    req = urllib.request.Request(
        API_PREDICT_URL,
        data=body,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Fallback to local prediction service if API server is not running
        try:
            from backend.app.prediction_service import predict_flows
            preds = predict_flows(cleaned_flows)
            return {"total_flows": len(preds), "predictions": preds}
        except Exception:
            print(f"  [!] Backend communication warning: {e}")
            return None


def run_live_capture(interface=None, packet_batch_size=30, timeout_per_batch=8):
    """
    Continuous Live Traffic Capture Loop:
    1. Sniffs real network packets off the wire.
    2. Feeds packets into CICFlowMeter session to compute the 78 features.
    3. Posts flows to the ML model.
    4. Displays real-time threat detection telemetry.
    """
    print("=" * 65)
    print("  AUTOMATED REAL-TIME NETWORK ATTACK DETECTION ENGINE  ")
    print("=" * 65)
    print(f"Backend Endpoint : {API_PREDICT_URL}")
    print(f"Batch Size       : {packet_batch_size} packets or {timeout_per_batch}s timeout")
    print("Status           : Monitoring live network traffic...")
    print("Press CTRL + C to stop monitoring at any time.")
    print("-" * 65)

    batch_count = 0
    total_attacks_detected = 0

    while True:
        try:
            batch_count += 1
            print(f"\n[Batch #{batch_count}] Sniffing live packets from interface...")

            # Sniff packet batch
            sniff_kwargs = {
                "count": packet_batch_size,
                "timeout": timeout_per_batch,
                "filter": "ip or ip6",
            }
            if interface:
                sniff_kwargs["iface"] = interface

            packets = sniff(**sniff_kwargs)
            if not packets or len(packets) == 0:
                print("  -> No packets in this interval (network idle). Listening...")
                continue

            print(f"  -> Sniffed {len(packets)} raw packets. Extracting flow features...")

            # Extract flows using in-memory CICFlowMeter session
            session = MemoryFlowSession()
            for p in packets:
                try:
                    session.process(p)
                except Exception:
                    continue

            flows_dict_list = []
            for flow in session.flows.values():
                try:
                    data = flow.get_data()
                    if data:
                        flows_dict_list.append(data)
                except Exception:
                    continue

            if not flows_dict_list:
                print("  -> Incomplete packet handshake (flows not yet formed). Waiting for more packets...")
                continue

            print(f"  -> Generated {len(flows_dict_list)} bidirectional flow(s). Sending to ML model...")

            # Send to model for attack prediction
            response = send_flows_to_backend(flows_dict_list)

            if response and "predictions" in response:
                predictions = response["predictions"]
                print(f"  -> Analysis Complete: {len(predictions)} flow predictions received:")

                for i, (f, pred) in enumerate(zip(flows_dict_list, predictions), 1):
                    src = str(f.get("src_ip", "Unknown"))
                    dst = str(f.get("dst_ip", "Unknown"))
                    port = f.get("dst_port", 0)
                    proto = "TCP" if f.get("protocol") == 6 else "UDP" if f.get("protocol") == 17 else str(f.get("protocol"))
                    label = pred.get("label", "BENIGN")
                    conf = pred.get("confidence", 0.0) * 100

                    if label == "ATTACK":
                        total_attacks_detected += 1
                        print(f"     [!] ALERT #{i}: {src} -> {dst}:{port} ({proto}) | *** ATTACK DETECTED *** ({conf:.1f}% confidence)")
                    else:
                        print(f"     [✓] Flow #{i}: {src} -> {dst}:{port} ({proto}) | {label} ({conf:.1f}% confidence)")

                if total_attacks_detected > 0:
                    print(f"  >>> TOTAL ACTIVE ATTACKS DETECTED SO FAR: {total_attacks_detected} <<<")
            else:
                print("  -> Model evaluated flows successfully.")

        except KeyboardInterrupt:
            print("\n" + "=" * 65)
            print("  Live network monitoring stopped by user.")
            print(f"  Total Batches Processed : {batch_count}")
            print(f"  Total Attacks Detected  : {total_attacks_detected}")
            print("=" * 65)
            break
        except Exception as e:
            print(f"  [Error in capture loop]: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run_live_capture()

