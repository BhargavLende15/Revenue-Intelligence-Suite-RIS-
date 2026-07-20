import pandas as pd
import numpy as np
import shap
import pickle
import os
import matplotlib
matplotlib.use('Agg') # Non-interactive backend to prevent GUI errors
import matplotlib.pyplot as plt
from models.demand_prediction import DemandPredictor, CATEGORY_MAP, REGION_MAP, CHANNEL_MAP

class SHAPExplainerManager:
    def __init__(self):
        self.explainer = None
        self.background_data = None
        self.model = None
        self.feature_names = ["category", "unit_price", "discount_percentage", "region_id", "sales_channel", "month_num"]
        
    def initialize(self, df):
        """
        Loads the trained demand model, prepares background data, and fits the SHAP TreeExplainer.
        """
        # Load demand model
        predictor = DemandPredictor()
        if not predictor.load_model():
            print("Training demand model first to compute SHAP...")
            predictor.train(df)
        self.model = predictor.model
        
        # Preprocess features to act as background data
        X, _ = predictor.preprocess_df(df)
        self.background_data = X
        
        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.model, data=self.background_data)
        
        # Save explainer artifacts
        os.makedirs("models/saved", exist_ok=True)
        with open("models/saved/shap_explainer.pkl", "wb") as f:
            pickle.dump({
                "explainer": self.explainer,
                "background_data": self.background_data,
                "feature_names": self.feature_names
            }, f)
            
        print("SHAP TreeExplainer initialized successfully.")

    def load_explainer(self):
        """
        Loads the SHAP explainer from disk.
        """
        path = "models/saved/shap_explainer.pkl"
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
                self.explainer = data["explainer"]
                self.background_data = data["background_data"]
                self.feature_names = data["feature_names"]
            return True
        return False

    def generate_static_summary_plot(self, df):
        """
        Generates and saves a SHAP summary plot (beeswarm) as an image in dashboard assets.
        """
        if self.explainer is None:
            if not self.load_explainer():
                self.initialize(df)
                
        # Generate SHAP values for a sample of the data to keep it fast
        sample_x = self.background_data.sample(min(200, len(self.background_data)), random_state=42)
        shap_values = self.explainer(sample_x)
        
        # Plot
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, sample_x, show=False)
        
        # Ensure target folder exists
        os.makedirs("assets", exist_ok=True)
        plt.tight_layout()
        plt.savefig("assets/shap_summary_plot.png", dpi=150)
        plt.close()
        print("SHAP summary plot saved to assets/shap_summary_plot.png")

    def get_global_importance(self, df):
        """
        Returns average absolute SHAP values for each feature to plot in Dash.
        """
        if self.explainer is None:
            if not self.load_explainer():
                self.initialize(df)
                
        # Sample for speed
        sample_x = self.background_data.sample(min(300, len(self.background_data)), random_state=42)
        # Use shap_values(sample_x) which returns a numpy array
        shap_vals = self.explainer.shap_values(sample_x, check_additivity=False)
        
        # Mean absolute SHAP values
        mean_abs_shap = np.abs(shap_vals).mean(axis=0)
        
        importance_df = pd.DataFrame({
            "Feature": ["Category", "Unit Price", "Discount %", "Region", "Sales Channel", "Month"],
            "SHAP Importance": mean_abs_shap
        })
        return importance_df.sort_values(by="SHAP Importance", ascending=True)

    def explain_local_prediction(self, category_str, unit_price, discount_pct, region_str, channel_str, month_num):
        """
        Computes SHAP values for a single transaction scenario.
        Returns a list of feature contributions for waterfall chart.
        """
        if self.explainer is None:
            if not self.load_explainer():
                raise FileNotFoundError("SHAP explainer not initialized.")
                
        cat_code = CATEGORY_MAP.get(category_str, 0)
        reg_code = REGION_MAP.get(region_str, 0)
        chan_code = CHANNEL_MAP.get(channel_str, 0)
        
        # Create single row dataframe
        x_input = pd.DataFrame([{
            "category": cat_code,
            "unit_price": float(unit_price),
            "discount_percentage": float(discount_pct),
            "region_id": reg_code,
            "sales_channel": chan_code,
            "month_num": int(month_num)
        }], columns=self.feature_names)
        
        # Compute shap values
        # For tree explainer on single row
        shap_val = self.explainer.shap_values(x_input, check_additivity=False)[0]
        
        # Retrieve base value (expected value)
        expected_val = self.explainer.expected_value
        if isinstance(expected_val, np.ndarray):
            expected_val = expected_val[0]
            
        features_clean = ["Category", "Unit Price", "Discount %", "Region", "Sales Channel", "Month"]
        raw_values = [category_str, f"${unit_price:,.2f}", f"{discount_pct*100:.1f}%", region_str, channel_str, f"Month {month_num}"]
        
        contributions = []
        for i in range(len(self.feature_names)):
            contributions.append({
                "feature": features_clean[i],
                "shap_value": float(shap_val[i]),
                "actual_value": str(raw_values[i])
            })
            
        return {
            "base_value": float(expected_val),
            "prediction": float(expected_val + sum(shap_val)),
            "contributions": contributions
        }
