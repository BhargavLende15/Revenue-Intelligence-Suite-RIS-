import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pickle
import os

class CustomerSegmenter:
    def __init__(self, n_clusters=4):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.cluster_names = {}
        
    def build_rfm_features(self, df):
        """
        Builds RFM + Discount + Return Rate features for each customer.
        """
        # Convert date column if it isn't
        df["order_date"] = pd.to_datetime(df["order_date"])
        max_date = df["order_date"].max()
        
        # Aggregate by customer
        cust_df = df.groupby(["customer_id", "customer_name", "customer_segment"]).agg({
            "order_date": lambda x: (max_date - x.max()).days, # Recency
            "order_id": "nunique", # Frequency
            "net_revenue": "sum", # Monetary
            "discount_percentage": "mean",
            "is_returned": "mean"
        }).reset_index()
        
        cust_df.rename(columns={
            "order_date": "recency",
            "order_id": "frequency",
            "net_revenue": "monetary"
        }, inplace=True)
        
        return cust_df

    def train(self, df):
        """
        Extracts features, normalizes, fits KMeans, and assigns names to clusters.
        """
        cust_df = self.build_rfm_features(df)
        
        features = ["recency", "frequency", "monetary", "discount_percentage", "is_returned"]
        X = cust_df[features].fillna(0.0)
        
        # Scale
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit K-Means
        self.kmeans.fit(X_scaled)
        cust_df["cluster"] = self.kmeans.labels_
        
        # Assign business personas to clusters dynamically based on cluster centers
        centers = self.scaler.inverse_transform(self.kmeans.cluster_centers_)
        centers_df = pd.DataFrame(centers, columns=features)
        centers_df["cluster"] = range(self.n_clusters)
        
        # Label clusters:
        # 1. High Return Risk: center with highest return rate
        return_risk_cluster = centers_df.sort_values(by="is_returned", ascending=False).iloc[0]["cluster"]
        
        # Remove return risk cluster from remaining
        remaining = centers_df[centers_df["cluster"] != return_risk_cluster]
        
        # 2. VIP High-Value: highest monetary value among remaining
        vip_cluster = remaining.sort_values(by="monetary", ascending=False).iloc[0]["cluster"]
        
        # Remove VIP from remaining
        remaining = remaining[remaining["cluster"] != vip_cluster]
        
        # 3. Discount Chasers: highest discount rate among remaining
        discount_chaser_cluster = remaining.sort_values(by="discount_percentage", ascending=False).iloc[0]["cluster"]
        
        # 4. Standard: last remaining
        standard_cluster = remaining[remaining["cluster"] != discount_chaser_cluster].iloc[0]["cluster"]
        
        self.cluster_names = {
            int(vip_cluster): "VIP High-Value",
            int(discount_chaser_cluster): "Discount Seekers",
            int(return_risk_cluster): "High Return Risk",
            int(standard_cluster): "Standard Customers"
        }
        
        cust_df["segment_name"] = cust_df["cluster"].map(self.cluster_names)
        
        # Save model artifacts
        os.makedirs("models/saved", exist_ok=True)
        with open("models/saved/segmenter.pkl", "wb") as f:
            pickle.dump({
                "kmeans": self.kmeans,
                "scaler": self.scaler,
                "cluster_names": self.cluster_names,
                "features": features
            }, f)
            
        return cust_df

    def load_model(self):
        """
        Loads the segmentation model from disk.
        """
        model_path = "models/saved/segmenter.pkl"
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                data = pickle.load(f)
                self.kmeans = data["kmeans"]
                self.scaler = data["scaler"]
                self.cluster_names = data["cluster_names"]
            return True
        return False
