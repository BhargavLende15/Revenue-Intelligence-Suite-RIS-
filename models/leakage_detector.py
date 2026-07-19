import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os

class LeakageAnomalyDetector:
    def __init__(self, contamination=0.06):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.feature_names = ["gross_revenue", "discount_percentage", "delay_days", "profit_margin", "is_returned"]
        
    def preprocess(self, df):
        """
        Prepares features for the Isolation Forest model.
        """
        X = df[self.feature_names].fillna(0.0).copy()
        return X

    def train(self, df):
        """
        Fits Isolation Forest model on the master dataset and tags anomalies.
        """
        X = self.preprocess(df)
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit model
        self.model.fit(X_scaled)
        
        # Save model
        os.makedirs("models/saved", exist_ok=True)
        with open("models/saved/leakage_detector.pkl", "wb") as f:
            pickle.dump({
                "model": self.model,
                "scaler": self.scaler,
                "features": self.feature_names
            }, f)
            
        return self.predict(df)

    def load_model(self):
        """
        Loads the anomaly detector model from disk.
        """
        model_path = "models/saved/leakage_detector.pkl"
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.scaler = data["scaler"]
                self.feature_names = data["features"]
            return True
        return False

    def predict(self, df):
        """
        Calculates anomaly scores and labels (1 = Normal, -1 = Anomalous/Leakage)
        """
        if self.model is None:
            if not self.load_model():
                raise FileNotFoundError("Leakage detection model not trained yet. Run train first.")
                
        X = self.preprocess(df)
        X_scaled = self.scaler.transform(X)
        
        scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)
        
        # Return dataframe copy with predictions added
        res_df = df.copy()
        # Invert predictions: 1 for normal, -1 for anomaly. Let's make it 1 for anomaly, 0 for normal for easy charting.
        res_df["anomaly_score"] = scores
        res_df["is_anomaly"] = np.where(predictions == -1, 1, 0)
        
        return res_df
