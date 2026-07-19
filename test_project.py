import os
import unittest
import pandas as pd
import sqlite3

class TestRevenueIntelligenceSuite(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Paths
        cls.raw_dir = "data/raw"
        cls.db_path = "database/revenue_intelligence.db"
        cls.models_dir = "models/saved"
        
    def test_01_data_generation(self):
        """Test that data generation runs and creates all 10 CSV files."""
        from etl.generate_data import generate_enterprise_data
        generate_enterprise_data()
        
        expected_files = [
            "customers.csv", "orders.csv", "order_items.csv", "products.csv", 
            "returns.csv", "discounts.csv", "regions.csv", "sales_representatives.csv", 
            "marketing_spend.csv", "monthly_targets.csv"
        ]
        
        for file in expected_files:
            file_path = os.path.join(self.raw_dir, file)
            self.assertTrue(os.path.exists(file_path), f"File {file} was not generated.")
            df = pd.read_csv(file_path)
            self.assertGreater(len(df), 0, f"File {file} is empty.")
            
    def test_02_etl_pipeline(self):
        """Test that ETL pipeline executes and populates SQLite database."""
        from etl.pipeline import run_etl_pipeline
        success = run_etl_pipeline()
        self.assertTrue(success, "ETL pipeline failed execution.")
        self.assertTrue(os.path.exists(self.db_path), "Database was not created.")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify master analytical table is populated
        cursor.execute("SELECT COUNT(*) FROM master_analytical_dataset;")
        row_count = cursor.fetchone()[0]
        self.assertGreater(row_count, 0, "master_analytical_dataset is empty.")
        
        # Verify views are present
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='view_monthly_summary';")
        self.assertIsNotNone(cursor.fetchone(), "view_monthly_summary was not created.")
        
        conn.close()

    def test_03_sql_analytics_queries(self):
        """Test that the SQL executor executes all files successfully."""
        from analytics.sql_executor import execute_sql_query
        
        sql_queries = [
            "top_customers", "top_products", "worst_products", 
            "revenue_by_region", "revenue_by_month", "revenue_leakage_by_category"
        ]
        
        for q in sql_queries:
            df = execute_sql_query(q)
            self.assertIsNotNone(df, f"Query '{q}' returned None.")
            self.assertGreater(len(df), 0, f"Query '{q}' returned no rows.")
            print(f" - SQL query '{q}' tested successfully. Columns: {list(df.columns)}")

    def test_04_machine_learning_models(self):
        """Test training of ML models: Forecasting, Demand, Segmentation, Leakage."""
        from analytics.sql_executor import run_raw_query
        df = run_raw_query("SELECT * FROM master_analytical_dataset")
        
        # Test Forecasting
        from models.forecasting import train_and_forecast_revenue
        history, forecast = train_and_forecast_revenue(df)
        self.assertGreater(len(forecast), 0, "Forecast dataframe is empty.")
        self.assertIn("forecasted_revenue", forecast.columns)
        
        # Test Demand Prediction Model
        from models.demand_prediction import DemandPredictor
        predictor = DemandPredictor()
        rmse, r2 = predictor.train(df)
        self.assertTrue(os.path.exists(os.path.join(self.models_dir, "demand_model.pkl")))
        
        # Test Customer Segmentation
        from models.segmentation import CustomerSegmenter
        segmenter = CustomerSegmenter()
        cust_df = segmenter.train(df)
        self.assertTrue(os.path.exists(os.path.join(self.models_dir, "segmenter.pkl")))
        self.assertIn("segment_name", cust_df.columns)
        
        # Test Leakage Anomaly Detection
        from models.leakage_detector import LeakageAnomalyDetector
        detector = LeakageAnomalyDetector()
        scored_df = detector.train(df)
        self.assertTrue(os.path.exists(os.path.join(self.models_dir, "leakage_detector.pkl")))
        self.assertIn("is_anomaly", scored_df.columns)

    def test_05_explainable_ai_shap(self):
        """Test SHAP explainer initialization and waterfall calculations."""
        from analytics.sql_executor import run_raw_query
        df = run_raw_query("SELECT * FROM master_analytical_dataset")
        
        from analytics.explainability import SHAPExplainerManager
        shap_manager = SHAPExplainerManager()
        shap_manager.initialize(df)
        self.assertTrue(os.path.exists(os.path.join(self.models_dir, "shap_explainer.pkl")))
        
        # Test local explanation
        r = df.iloc[0]
        local_explanation = shap_manager.explain_local_prediction(
            category_str=r["category"],
            unit_price=float(r["unit_price"]),
            discount_pct=float(r["discount_percentage"]),
            region_str=r["region_name"],
            channel_str=r["sales_channel"],
            month_num=int(r["month_num"])
        )
        self.assertIn("base_value", local_explanation)
        self.assertIn("contributions", local_explanation)
        self.assertEqual(len(local_explanation["contributions"]), len(shap_manager.feature_names))

if __name__ == "__main__":
    unittest.main()
