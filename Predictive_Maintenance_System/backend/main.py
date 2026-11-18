from datetime import datetime
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db, get_database_status
from backend.models_db import PredictionRecord

# --------------------------------------------------
# 1. Create FastAPI application & CORS
# --------------------------------------------------

app = FastAPI(
    title="Predictive Maintenance API",
    description="Predict machine failure using machine learning with persistent MySQL database logging.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 2. Load saved model files
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "models"

try:
    best_model = joblib.load(MODEL_DIR / "best_model.pkl")
    best_model_name = joblib.load(MODEL_DIR / "best_model_name.pkl")
    feature_columns = joblib.load(MODEL_DIR / "feature_columns.pkl")
    model_input_columns = joblib.load(MODEL_DIR / "model_input_columns.pkl")
    model_input_type = joblib.load(MODEL_DIR / "model_input_type.pkl")

    scaler = None
    if model_input_type == "scaled":
        scaler = joblib.load(MODEL_DIR / "scaler.pkl")

except Exception as error:
    raise RuntimeError(
        f"Could not load model files from {MODEL_DIR}. "
        "Run Phase 4 first and verify the saved files."
    ) from error


# --------------------------------------------------
# 3. Pydantic Schemas
# --------------------------------------------------

class MachineInput(BaseModel):
    machine_type: Literal["L", "M", "H"] = Field(
        description="Machine quality type: L, M, or H"
    )
    air_temperature: float = Field(
        gt=0,
        description="Air temperature in Kelvin"
    )
    process_temperature: float = Field(
        gt=0,
        description="Process temperature in Kelvin"
    )
    rotational_speed: int = Field(
        gt=0,
        description="Rotational speed in rpm"
    )
    torque: float = Field(
        gt=0,
        description="Torque in Nm"
    )
    tool_wear: int = Field(
        ge=0,
        description="Tool wear in minutes"
    )


# --------------------------------------------------
# 4. Input Preparation
# --------------------------------------------------

def clean_xgb_columns(columns):
    return (
        columns.astype(str)
        .str.replace("[", "_", regex=False)
        .str.replace("]", "_", regex=False)
        .str.replace("<", "_", regex=False)
    )


def prepare_input(machine: MachineInput):
    # Build input row matching Phase 3 encoding
    input_data = pd.DataFrame([{
        "Air temperature [K]": machine.air_temperature,
        "Process temperature [K]": machine.process_temperature,
        "Rotational speed [rpm]": machine.rotational_speed,
        "Torque [Nm]": machine.torque,
        "Tool wear [min]": machine.tool_wear,
        # Phase 3 dropped H as reference category
        "Type_L": int(machine.machine_type == "L"),
        "Type_M": int(machine.machine_type == "M")
    }])

    input_data = input_data.reindex(
        columns=feature_columns,
        fill_value=0
    )

    if model_input_type == "scaled" and scaler is not None:
        input_data = scaler.transform(input_data)
    elif best_model_name == "XGBoost":
        input_data.columns = clean_xgb_columns(input_data.columns)
        input_data = input_data.reindex(columns=model_input_columns, fill_value=0)
    else:
        input_data = input_data.reindex(columns=model_input_columns, fill_value=0)

    return input_data


# --------------------------------------------------
# 5. API Endpoints
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Predictive Maintenance API is running",
        "model": best_model_name,
        "database": get_database_status()
    }


@app.get("/model-info")
def model_info():
    return {
        "model_name": best_model_name,
        "input_features": len(feature_columns),
        "status": "loaded"
    }


@app.get("/database-status")
def database_status():
    return get_database_status()


@app.post("/predict")
def predict_failure(
    machine: MachineInput,
    save: bool = Query(True, description="Whether to persist this prediction into MySQL"),
    db: Session = Depends(get_db)
):
    try:
        input_data = prepare_input(machine)

        prediction = int(best_model.predict(input_data)[0])
        failure_probability = float(best_model.predict_proba(input_data)[0][1])
        result_text = "Failure predicted" if prediction == 1 else "No failure predicted"
        prob_percentage = round(failure_probability * 100, 2)

        record_id = None
        created_iso = datetime.utcnow().isoformat()

        if save:
            try:
                record = PredictionRecord(
                    machine_type=machine.machine_type,
                    air_temperature=machine.air_temperature,
                    process_temperature=machine.process_temperature,
                    rotational_speed=machine.rotational_speed,
                    torque=machine.torque,
                    tool_wear=machine.tool_wear,
                    prediction=prediction,
                    result=result_text,
                    failure_probability=prob_percentage,
                    model_name=str(best_model_name)
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                record_id = record.id
                if record.created_at:
                    created_iso = record.created_at.isoformat()
            except Exception as db_err:
                db.rollback()
                print(f"[Database Error] Could not save prediction record: {db_err}")

        return {
            "id": record_id,
            "machine_type": machine.machine_type,
            "prediction": prediction,
            "result": result_text,
            "failure_probability": prob_percentage,
            "model_name": best_model_name,
            "created_at": created_iso,
            "time": created_iso
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        ) from error


@app.get("/history")
def get_prediction_history(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Fetch persistent prediction logs from MySQL / Database.
    """
    try:
        records = (
            db.query(PredictionRecord)
            .order_by(PredictionRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in records]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve history from database: {str(e)}"
        )


@app.delete("/history")
def clear_prediction_history(db: Session = Depends(get_db)):
    """
    Clear all prediction logs from the database.
    """
    try:
        deleted_count = db.query(PredictionRecord).delete()
        db.commit()
        return {
            "message": "Prediction history cleared successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Could not clear history: {str(e)}"
        )
