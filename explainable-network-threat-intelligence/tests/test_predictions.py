"""
Unit tests for Phase 8: Live Attack Prediction
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.predict import (
    load_model_and_features,
    prepare_live_features,
    predict_live_flows,
    FEATURE_MAPPING
)


class TestLivePredictions(unittest.TestCase):

    def test_load_model_and_features(self):
        """Verify that model and the 78 feature columns load correctly."""
        model, features = load_model_and_features(
            model_path="models/network_model.joblib",
            features_path="models/feature_columns.joblib"
        )
        self.assertIsNotNone(model)
        self.assertEqual(len(features), 78)
        self.assertIn("Destination Port", features)
        self.assertIn("Flow Duration", features)

    def test_prepare_live_features(self):
        """Verify that feature mapping, time unit conversion, and NaN/inf handling work correctly."""
        _, features = load_model_and_features()
        live_df = pd.read_csv("data/processed/live_flows.csv")

        X_live = prepare_live_features(live_df, features)

        # Check shape
        self.assertEqual(X_live.shape, (len(live_df), 78))

        # Check column order
        self.assertEqual(list(X_live.columns), features)

        # Check that no NaNs or Infs exist
        self.assertEqual(X_live.isnull().sum().sum(), 0)
        self.assertEqual(np.isinf(X_live.values).sum(), 0)

        # Check non-negativity
        self.assertEqual((X_live < 0).sum().sum(), 0)

    def test_predict_live_flows(self):
        """Verify end-to-end prediction, uncertainty calculation, and status assignment."""
        results = predict_live_flows(confidence_threshold=0.70)

        self.assertEqual(len(results), 6)
        for col in ["prediction", "label", "confidence", "uncertainty", "status"]:
            self.assertIn(col, results.columns)

        # Verify uncertainty + confidence = 1.0
        total = results["confidence"] + results["uncertainty"]
        np.testing.assert_allclose(total, 1.0, atol=1e-3)

        # Verify labels match predictions
        for _, row in results.iterrows():
            expected_label = "ATTACK" if row["prediction"] == 1 else "BENIGN"
            self.assertEqual(row["label"], expected_label)

            if row["confidence"] >= 0.70:
                self.assertEqual(row["status"], "High Confidence")
            else:
                self.assertIn("Low Confidence", row["status"])


if __name__ == "__main__":
    unittest.main()
