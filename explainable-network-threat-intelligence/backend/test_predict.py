import json
import urllib.request
import urllib.error
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.prediction_service import feature_mapping, time_features

MODELS = Path(__file__).resolve().parent.parent / "models"
URL = "http://127.0.0.1:8000/predict"

feature_columns = list(joblib.load(MODELS / "feature_columns.joblib"))
X_test = joblib.load(MODELS / "X_test.joblib")
y_test = np.asarray(joblib.load(MODELS / "y_test.joblib")).ravel()

if not isinstance(X_test, pd.DataFrame):
    X_test = pd.DataFrame(X_test, columns=feature_columns)

# 3 real ATTACK rows and 3 real BENIGN rows
attack_idx = np.where(y_test == 1)[0][:3]
benign_idx = np.where(y_test == 0)[0][:3]
chosen = list(attack_idx) + list(benign_idx)
true_labels = ["ATTACK"] * len(attack_idx) + ["BENIGN"] * len(benign_idx)

flows = []
for i in chosen:
    row = X_test.iloc[i]
    flow = {}
    for col in feature_columns:
        value = float(row[col])
        if not np.isfinite(value):
            value = 0.0
        # Send time values in seconds, like live capture does
        if col in time_features:
            value = value / 1_000_000.0
        flow[feature_mapping[col]] = value
    flows.append(flow)

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
    raise SystemExit(1)

print(f"{'TRUE':8} {'PREDICTED':10} {'CONF':>8} {'UNCERT':>8}  STATUS")
for true, p in zip(true_labels, result["predictions"]):
    print(
        f"{true:8} {p['label']:10} "
        f"{p['confidence']*100:7.2f}% {p['uncertainty']*100:7.2f}%  {p['status']}"
    )