import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score
import pickle
import os

# Define encoder maps for consistency across model training, SHAP, and dashboard inputs
CATEGORY_MAP = {"Software": 0, "Hardware": 1, "Consulting": 2, "Support": 3}
REGION_MAP = {"North America": 0, "Europe": 1, "Asia-Pacific": 2, "Latin America": 3}
CHANNEL_MAP = {"Direct": 0, "Online": 1, "Partner": 2}

REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP.items()}
REVERSE_REGION_MAP = {v: k for k, v in REGION_MAP.items()}
REVERSE_CHANNEL_MAP = {v: k for k, v in CHANNEL_MAP.items()}

class DemandPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = ["category", "unit_price", "discount_percentage", "region_id", "sales_channel", "month_num"]
        
    def preprocess_df(self, df):
        """
        Preprocesses and encodes categorical features from the master dataframe.
        """
        model_df = df.copy()
        
        # Apply mappings
        model_df["category_encoded"] = model_df["category"].map(CATEGORY_MAP).fillna(-1)
        model_df["region_encoded"] = model_df["region_name"].map(REGION_MAP).fillna(-1)
        model_df["channel_encoded"] = model_df["sales_channel"].map(CHANNEL_MAP).fillna(-1)
        
        # Prepare final columns
        X_df = pd.DataFrame({
            "category": model_df["category_encoded"],
            "unit_price": model_df["unit_price"].fillna(0.0),
            "discount_percentage": model_df["discount_percentage"].fillna(0.0),
            "region_id": model_df["region_encoded"],
            "sales_channel": model_df["channel_encoded"],
            "month_num": model_df["month_num"].fillna(1)
        })
        
        y = model_df["quantity"].fillna(1.0)
        return X_df, y

    def train(self, df):
        """
        Preprocesses, trains the Random Forest model, and saves the artifacts.
        """
        X, y = self.preprocess_df(df)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest Regressor
        self.model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=8)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        preds = self.model.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        print(f"Random Forest Demand Model Trained. RMSE: {rmse:.4f}, R2 Score: {r2:.4f}")
        
        # Save model to disk
        os.makedirs("models/saved", exist_ok=True)
        with open("models/saved/demand_model.pkl", "wb") as f:
            pickle.dump(self.model, f)
            
        return rmse, r2

    def load_model(self):
        """
        Loads the trained model from disk.
        """
        model_path = "models/saved/demand_model.pkl"
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            return True
        return False

    def predict_demand(self, category_str, unit_price, discount_pct, region_str, channel_str, month_num):
        """
        Predicts demand for a single set of inputs (used in dashboard simulator).
        """
        if self.model is None:
            if not self.load_model():
                raise FileNotFoundError("Model not trained yet. Run train first.")
                
        cat_code = CATEGORY_MAP.get(category_str, 0)
        reg_code = REGION_MAP.get(region_str, 0)
        chan_code = CHANNEL_MAP.get(channel_str, 0)
        
        X_input = pd.DataFrame([{
            "category": cat_code,
            "unit_price": float(unit_price),
            "discount_percentage": float(discount_pct),
            "region_id": reg_code,
            "sales_channel": chan_code,
            "month_num": int(month_num)
        }], columns=self.feature_names)
        
        pred_qty = self.model.predict(X_input)[0]
        return max(1.0, round(pred_qty, 2))
