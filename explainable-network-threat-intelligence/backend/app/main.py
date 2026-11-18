from app.database_service import save_predictions
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    PredictionRequest,
    PredictionResponse,
    ExplanationRequest,
    ExplanationResponse
)
from app.prediction_service import predict_flows
from app.explanation_service import generate_flow_explanation

from sqlalchemy import func
from app.database import SessionLocal
from app.db_models import NetworkFlow, AttackPrediction

app = FastAPI(
    title="Explainable Network Threat Intelligence System",
    description="ML-Based Network Attack Detection API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {
        "message": "Welcome to Network Threat Intelligence System",
        "status": "Backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "Healthy",
        "message": "FastAPI backend is working"
    }


def save_predictions_to_csv(flows, results):
    """Persist new flow predictions to CSV cache so dashboard updates in real time."""
    try:
        import os
        import pandas as pd

        candidates_preds = [
            os.path.join("data", "processed", "live_prediction_results.csv"),
            os.path.join("..", "data", "processed", "live_prediction_results.csv"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_prediction_results.csv"))
        ]
        preds_path = next((p for p in candidates_preds if os.path.exists(p)), candidates_preds[-1])

        candidates_live = [
            os.path.join("data", "processed", "live_flows.csv"),
            os.path.join("..", "data", "processed", "live_flows.csv"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_flows.csv"))
        ]
        live_path = next((p for p in candidates_live if os.path.exists(p)), candidates_live[-1])

        # 1. Update live_prediction_results.csv
        new_preds = []
        for flow, res in zip(flows, results):
            new_preds.append({
                "flow_id": 0,
                "src_ip": flow.get("src_ip", "Unknown"),
                "dst_ip": flow.get("dst_ip", "Unknown"),
                "src_port": flow.get("src_port", 0),
                "dst_port": flow.get("dst_port", 0),
                "protocol": "TCP" if flow.get("protocol") == 6 else "UDP" if flow.get("protocol") == 17 else str(flow.get("protocol", "TCP")),
                "prediction": res.get("prediction", 0),
                "label": res.get("label", "BENIGN"),
                "prob_benign": round(1.0 - res.get("confidence", 0.0) if res.get("prediction") == 1 else res.get("confidence", 0.0), 4),
                "prob_attack": round(res.get("confidence", 0.0) if res.get("prediction") == 1 else 1.0 - res.get("confidence", 0.0), 4),
                "confidence": round(res.get("confidence", 0.0), 4),
                "uncertainty": round(res.get("uncertainty", 0.0), 4),
                "status": res.get("status", "High Confidence")
            })

        if os.path.exists(preds_path):
            existing_df = pd.read_csv(preds_path)
            max_id = int(existing_df["flow_id"].max()) if not existing_df.empty and "flow_id" in existing_df.columns else 0
        else:
            existing_df = pd.DataFrame()
            max_id = 0

        # Assign strictly increasing permanent IDs to newly arriving flows
        for i, pred in enumerate(new_preds):
            pred["flow_id"] = max_id + i + 1

        new_preds_df = pd.DataFrame(new_preds)
        if not existing_df.empty:
            combined_df = pd.concat([new_preds_df, existing_df], ignore_index=True)
        else:
            combined_df = new_preds_df

        # Keep up to 10,000 recent flows in cache (eliminates the 100-packet ceiling)
        combined_df.head(10000).to_csv(preds_path, index=False)

        # 2. Update live_flows.csv
        new_flows_df = pd.DataFrame(flows)
        if os.path.exists(live_path):
            existing_flows_df = pd.read_csv(live_path)
            combined_flows = pd.concat([new_flows_df, existing_flows_df], ignore_index=True)
        else:
            combined_flows = new_flows_df
        combined_flows.head(10000).to_csv(live_path, index=False)
    except Exception as e:
        print(f"[!] Warning updating CSV cache: {e}")


def inject_simulation_flow(is_attack: bool = True):
    """Inject a realistic CIC-IDS2017 flow (Benign or Attack) directly into the pipeline."""
    import os
    import sys
    import random
    from pathlib import Path
    import joblib
    import numpy as np
    import pandas as pd

    # Resolve project root
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.predict import FEATURE_MAPPING, TIME_FEATURES

    models_dir = project_root / "models"
    feature_columns = list(joblib.load(models_dir / "feature_columns.joblib"))
    X_test = joblib.load(models_dir / "X_test.joblib")
    y_test = np.asarray(joblib.load(models_dir / "y_test.joblib")).ravel()

    if not isinstance(X_test, pd.DataFrame):
        X_test = pd.DataFrame(X_test, columns=feature_columns)

    target_label = 1 if is_attack else 0
    indices = np.where(y_test == target_label)[0]
    chosen_idx = random.choice(indices)
    row = X_test.iloc[chosen_idx]

    random_src_port = random.randint(45000, 65000)
    attacker_ips = ["192.168.1.105 (Attacker)", "172.16.0.45 (Botnet)", "10.0.0.99 (Infiltrator)", "185.220.101.5 (PortScan)"]
    benign_ips = ["192.168.1.50 (User PC)", "192.168.1.25 (Workstation)", "10.203.56.81 (Localhost)", "192.168.1.12 (Laptop)"]

    src_ip = random.choice(attacker_ips) if is_attack else random.choice(benign_ips)
    dst_ip = "192.168.1.1 (Server Target)" if is_attack else "142.250.190.46 (Google HTTPS)"

    flow_dict = {
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": random_src_port,
        "dst_port": 80 if is_attack else 443,
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

    results = predict_flows([flow_dict])
    save_predictions_to_csv([flow_dict], results)
    return results[0]


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        results = predict_flows(request.flows)

        # 1. Save predictions into MySQL if available
        try:
            save_predictions(request.flows, results)
        except Exception:
            pass  # MySQL offline/unreachable; fallback handles persistence

        # 2. Persist to live CSV cache so dashboard updates instantly
        save_predictions_to_csv(request.flows, results)

        return {
            "total_flows": len(results),
            "predictions": results
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(exc)}"
        )


@app.post("/attack/trigger")
def trigger_attack():
    """One-click trigger to simulate and analyze a live network attack."""
    try:
        flow_result = inject_simulation_flow(is_attack=True)
        return {
            "status": "success",
            "message": "Live attack packet injected and detected by Random Forest model!",
            "prediction": flow_result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/traffic/simulate-benign")
def simulate_benign():
    """One-click trigger to simulate normal safe user browsing traffic."""
    try:
        flow_result = inject_simulation_flow(is_attack=False)
        return {
            "status": "success",
            "message": "Normal benign traffic packet processed successfully!",
            "prediction": flow_result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/dashboard/reset")
def reset_dashboard():
    """Reset live flows cache to a clean baseline."""
    try:
        import os
        import pandas as pd
        preds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_prediction_results.csv"))
        live_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_flows.csv"))

        if os.path.exists(preds_path):
            df = pd.read_csv(preds_path)
            if len(df) > 6:
                clean_df = df.tail(6).copy()
                clean_df["flow_id"] = range(1, len(clean_df) + 1)
                clean_df.to_csv(preds_path, index=False)

        if os.path.exists(live_path):
            flows_df = pd.read_csv(live_path)
            if len(flows_df) > 6:
                flows_df.tail(6).to_csv(live_path, index=False)

        return {"status": "success", "message": "Dashboard cache reset to clean baseline."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
@app.post("/explain", response_model=ExplanationResponse)
def explain(request: ExplanationRequest):
    try:
        explanation = generate_flow_explanation(
            flow_data=request.flow,
            method=request.method,
            top_n=request.top_n
        )
        return explanation
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(exc)}")


@app.get("/flows/explainable")
def get_explainable_flows():
    """
    Returns live captured flows with their full feature sets,
    enabling one-click selection on the Explainability dashboard.
    """
    import os
    import pandas as pd

    # Check potential relative paths
    candidates = [
        os.path.join("data", "processed", "live_flows.csv"),
        os.path.join("..", "data", "processed", "live_flows.csv"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_flows.csv"))
    ]
    flows_path = next((p for p in candidates if os.path.exists(p)), None)

    if not flows_path:
        return {"total": 0, "flows": []}

    preds_path = os.path.join(os.path.dirname(flows_path), "live_prediction_results.csv")

    flows_df = pd.read_csv(flows_path)
    preds_df = pd.read_csv(preds_path) if os.path.exists(preds_path) else None

    proto_map = {6: "TCP", 17: "UDP"}
    items = []
    for idx, row in flows_df.iterrows():
        flow_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        proto_val = row.get("protocol", "Unknown")
        proto_name = proto_map.get(proto_val, str(proto_val))

        label = "BENIGN"
        confidence = 0.95
        if preds_df is not None and idx < len(preds_df):
            label = str(preds_df.iloc[idx].get("label", "BENIGN"))
            confidence = float(preds_df.iloc[idx].get("confidence", 0.95))

        items.append({
            "flow_id": idx + 1,
            "src_ip": str(row.get("src_ip", "N/A")),
            "dst_ip": str(row.get("dst_ip", "N/A")),
            "src_port": int(row.get("src_port", 0)),
            "dst_port": int(row.get("dst_port", 0)),
            "protocol": proto_name,
            "label": label,
            "confidence": confidence,
            "features": flow_dict
        })

    return {"total": len(items), "flows": items}


@app.get("/dashboard/summary")
def dashboard_summary():
    # 1. Try querying MySQL if available
    try:
        db = SessionLocal()
        try:
            total_flows = db.query(func.count(NetworkFlow.flow_id)).scalar()
            benign_count = db.query(func.count(AttackPrediction.prediction_id)).filter(
                AttackPrediction.prediction == 0
            ).scalar()
            attack_count = db.query(func.count(AttackPrediction.prediction_id)).filter(
                AttackPrediction.prediction == 1
            ).scalar()
            avg_confidence = db.query(func.avg(AttackPrediction.confidence)).scalar()

            if total_flows and total_flows > 0:
                return {
                    "total_flows": total_flows or 0,
                    "benign_count": benign_count or 0,
                    "attack_count": attack_count or 0,
                    "average_confidence": round(avg_confidence or 0, 4),
                    "storage": "MySQL"
                }
        finally:
            db.close()
    except Exception:
        pass  # MySQL offline or not yet initialized; fallback to live results file

    # 2. Fallback: read from processed live prediction results file
    import os
    import pandas as pd

    candidates = [
        os.path.join("data", "processed", "live_prediction_results.csv"),
        os.path.join("..", "data", "processed", "live_prediction_results.csv"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_prediction_results.csv"))
    ]
    preds_path = next((p for p in candidates if os.path.exists(p)), None)

    if preds_path and os.path.exists(preds_path):
        df = pd.read_csv(preds_path)
        benign = int((df["prediction"] == 0).sum())
        attack = int((df["prediction"] == 1).sum())
        avg_conf = float(df["confidence"].mean())
        total_count = int(df["flow_id"].max()) if not df.empty and "flow_id" in df.columns else len(df)
        return {
            "total_flows": total_count,
            "benign_count": benign,
            "attack_count": attack,
            "average_confidence": round(avg_conf, 4),
            "storage": "Live Cache"
        }

    return {
        "total_flows": 0,
        "benign_count": 0,
        "attack_count": 0,
        "average_confidence": 0.0,
        "storage": "None"
    }


@app.get("/flows/recent")
def recent_flows():
    # 1. Try querying MySQL if available
    try:
        db = SessionLocal()
        try:
            results = (
                db.query(NetworkFlow, AttackPrediction)
                .join(
                    AttackPrediction,
                    NetworkFlow.flow_id == AttackPrediction.flow_id
                )
                .order_by(
                    AttackPrediction.predicted_at.desc(),
                    AttackPrediction.prediction_id.desc()
                )
                .limit(10)
                .all()
            )

            if results:
                predictions = []
                for flow, prediction in results:
                    predictions.append({
                        "flow_id": flow.flow_id,
                        "source_ip": flow.source_ip,
                        "destination_ip": flow.destination_ip,
                        "protocol": flow.protocol,
                        "label": prediction.label,
                        "confidence": prediction.confidence,
                        "uncertainty": prediction.uncertainty,
                        "status": prediction.status,
                        "predicted_at": str(prediction.predicted_at)
                    })

                return {
                    "total": len(predictions),
                    "predictions": predictions
                }
        finally:
            db.close()
    except Exception:
        pass  # MySQL offline; fallback to live results file

    # 2. Fallback: read from live prediction results file
    import os
    import pandas as pd

    candidates = [
        os.path.join("data", "processed", "live_prediction_results.csv"),
        os.path.join("..", "data", "processed", "live_prediction_results.csv"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "live_prediction_results.csv"))
    ]
    preds_path = next((p for p in candidates if os.path.exists(p)), None)

    if preds_path and os.path.exists(preds_path):
        df = pd.read_csv(preds_path)
        predictions = []
        for idx, row in df.head(15).iterrows():
            predictions.append({
                "flow_id": int(row.get("flow_id", idx + 1)),
                "source_ip": str(row.get("src_ip", "N/A")),
                "destination_ip": str(row.get("dst_ip", "N/A")),
                "protocol": str(row.get("protocol", "TCP")),
                "label": str(row.get("label", "BENIGN")),
                "confidence": float(row.get("confidence", 0.95)),
                "uncertainty": float(row.get("uncertainty", 0.05)),
                "status": str(row.get("status", "High Confidence")),
                "predicted_at": "Live Stream"
            })

        return {
            "total": len(predictions),
            "predictions": predictions
        }

    return {
        "total": 0,
        "predictions": []
    }
