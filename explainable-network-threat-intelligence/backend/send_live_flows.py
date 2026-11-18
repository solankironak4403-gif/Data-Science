import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

import numpy as np
import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "live_flows_v3.csv"
URL = "http://127.0.0.1:8000/predict"

# How many flows to send (change this number if you want)
LIMIT = 20

df = pd.read_csv(CSV)
print(f"CSV rows: {len(df)}")

df = df.head(LIMIT)
df = df.replace([np.inf, -np.inf], 0).fillna(0)

# Convert the table to a list of dictionaries (one per flow)
flows = json.loads(df.to_json(orient="records"))

body = json.dumps({"flows": flows}).encode("utf-8")
req = urllib.request.Request(
    URL, data=body, headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("HTTP error:", e.code)
    print(e.read().decode("utf-8"))
    sys.exit(1)

print(f"Sent {len(flows)} flows. Backend returned {result['total_flows']} predictions.")
print(f"{'SRC IP':40} {'DST IP':40} {'LABEL':8} {'CONF':>7}")
for flow, p in zip(flows, result["predictions"]):
    print(
        f"{str(flow.get('src_ip')):40} {str(flow.get('dst_ip')):40} "
        f"{p['label']:8} {p['confidence']*100:6.2f}%"
    )