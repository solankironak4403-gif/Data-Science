
import joblib
from pathlib import Path

# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Model file paths
MODEL_PATH = PROJECT_ROOT / "models" / "network_model.joblib"
FEATURE_PATH = PROJECT_ROOT / "models" / "feature_columns.joblib"

# Load trained Random Forest model
model = joblib.load(MODEL_PATH)

# Load feature column names
feature_columns = joblib.load(FEATURE_PATH)

# Display model information
print("Random Forest model loaded successfully!")
print("Total features:", len(feature_columns))
print("Model expected features:", model.n_features_in_)
