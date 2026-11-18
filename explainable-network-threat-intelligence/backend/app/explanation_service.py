"""
Explanation Service for FastAPI Backend
Provides local SHAP and LIME feature explanations for network flows.
"""

import os
import sys

# Ensure root directory is accessible for src module imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.explain import explain_flow_shap, explain_flow_lime


def generate_flow_explanation(flow_data: dict, method: str = "shap", top_n: int = 10) -> dict:
    """
    Generate an explanation for a given network flow using SHAP or LIME.

    Parameters:
    - flow_data: dict containing flow features (CICFlowMeter keys or model features)
    - method: 'shap' (default) or 'lime'
    - top_n: number of top features to return (default: 10)

    Returns:
    - dict with prediction label, confidence, base value, and ranked feature contributions.
    """
    method = method.strip().lower()

    if method == "lime":
        return explain_flow_lime(flow_data, top_n=top_n)
    elif method == "shap":
        return explain_flow_shap(flow_data, top_n=top_n)
    else:
        raise ValueError(f"Unsupported explanation method '{method}'. Choose 'shap' or 'lime'.")

