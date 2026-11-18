from pydantic import BaseModel, Field
from typing import Any, Optional


# Input received by the prediction API
class PredictionRequest(BaseModel):
    flows: list[dict[str, Any]] = Field(min_length=1)


# Prediction result for each network flow
class FlowPrediction(BaseModel):
    flow_id: int
    prediction: int
    label: str
    confidence: float
    uncertainty: float
    status: str


# Final API response
class PredictionResponse(BaseModel):
    total_flows: int
    predictions: list[FlowPrediction]


# Input received by the explanation API
class ExplanationRequest(BaseModel):
    flow: dict[str, Any] = Field(..., description="Flow features (dict)")
    method: str = Field(default="shap", description="Explanation method: 'shap' or 'lime'")
    top_n: int = Field(default=10, ge=1, le=30, description="Number of top features to return")


class FeatureContribution(BaseModel):
    feature: str
    value: Optional[float] = None
    importance: float
    effect: str


class ExplanationResponse(BaseModel):
    method: str
    prediction: int
    label: str
    confidence: float
    attack_probability: float
    benign_probability: float
    base_value: Optional[float] = None
    top_features: list[FeatureContribution]
