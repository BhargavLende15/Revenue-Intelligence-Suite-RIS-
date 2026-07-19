import os
import sqlite3
import pandas as pd
import numpy as np

def run_etl_pipeline():
    print("Starting ETL Pipeline...")
    raw_dir = "data/raw"
    db_dir = "database"
    os.makedirs(db_dir, exist_ok=True)
    db_path = f"{db_dir}/revenue_intelligence.db"

    # ==========================================
    # STEP 1: EXTRACT
    # ==========================================
    print("Step 1: Extracting raw CSV files...")
    try:
        customers = pd.read_csv(f"{raw_dir}/customers.csv")
        products = pd.read_csv(f"{raw_dir}/products.csv")
        regions = pd.read_csv(f"{raw_dir}/regions.csv")
        reps = pd.read_csv(f"{raw_dir}/sales_representatives.csv")
        orders = pd.read_csv(f"{raw_dir}/orders.csv")
        order_items = pd.read_csv(f"{raw_dir}/order_items.csv")
        discounts = pd.read_csv(f"{raw_dir}/discounts.csv")
        returns = pd.read_csv(f"{raw_dir}/returns.csv")
        marketing_spend = pd.read_csv(f"{raw_dir}/marketing_spend.csv")
        monthly_targets = pd.read_csv(f"{raw_dir}/monthly_targets.csv")
    except FileNotFoundError as e:
        print(f"Error: Missing raw CSV files. Run generate_data.py first. {e}")
        return False

    # ==========================================
    # STEP 2: VALIDATE
    # ==========================================
    print("Step 2: Validating schemas and datatypes...")
    
    validation_schemas = {
        "customers": {"cols": ["customer_id", "customer_name", "customer_segment", "created_date"], "types": {"customer_id": "object", "customer_segment": "object"}},
        "products": {"cols": ["product_id", "product_name", "category", "base_price", "cost_price"], "types": {"base_price": "float64", "cost_price": "float64"}},
        "regions": {"cols": ["region_id", "region_name", "country"], "types": {"region_id": "object"}},
        "reps": {"cols": ["sales_rep_id", "sales_rep_name", "region_id"], "types": {"sales_rep_id": "object"}},
        "orders": {"cols": ["order_id", "customer_id", "sales_rep_id", "region_id", "order_date", "shipping_date", "order_status", "sales_channel", "delay_days"], "types": {"order_id": "object", "delay_days": "int64"}},
        "order_items": {"cols": ["order_item_id", "order_id", "product_id", "quantity", "unit_price"], "types": {"quantity": "int64", "unit_price": "float64"}},
        "discounts": {"cols": ["discount_id", "order_id", "discount_percentage", "discount_code"], "types": {"discount_percentage": "float64"}},
        "returns": {"cols": ["return_id", "order_id", "return_date", "return_reason"], "types": {"return_id": "object"}},
        "marketing_spend": {"cols": ["spend_id", "region_id", "campaign_month", "marketing_channel", "spend_amount"], "types": {"spend_amount": "float64"}},
        "monthly_targets": {"cols": ["target_id", "region_id", "target_month", "target_revenue"], "types": {"target_revenue": "float64"}}
    }

    validation_errors = []
    for name, schema in validation_schemas.items():
        df = locals()[name]
        # Check columns
        missing_cols = [c for c in schema["cols"] if c not in df.columns]
        if missing_cols:
            validation_errors.append(f"Table '{name}' is missing columns: {missing_cols}")
            
        # Check datatypes for select columns
        for col, expected_type in schema["types"].items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if expected_type == "float64" and "float" not in actual_type:
                    validation_errors.append(f"Table '{name}', Column '{col}': expected float, got {actual_type}")
                elif expected_type == "int64" and "int" not in actual_type:
                    validation_errors.append(f"Table '{name}', Column '{col}': expected int, got {actual_type}")
                elif expected_type == "object" and actual_type not in ["object", "string", "str"]:
                    validation_errors.append(f"Table '{name}', Column '{col}': expected string/object, got {actual_type}")

    if validation_errors:
        print("Schema validation failed with errors:")
        for err in validation_errors:
            print(f" - {err}")
        return False
    print("Schema validation passed successfully!")

    # ==========================================
    # STEP 3: CLEAN
    # ==========================================
    print("Step 3: Cleaning data...")
    
    # Remove duplicates
    for name in validation_schemas.keys():
        df = locals()[name]
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        if before > after:
            print(f" - Removed {before - after} duplicates from table '{name}'")
        # Save back the cleaned df
        locals()[name] = df

    # Standardize dates
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["shipping_date"] = pd.to_datetime(orders["shipping_date"])
    customers["created_date"] = pd.to_datetime(customers["created_date"])
    returns["return_date"] = pd.to_datetime(returns["return_date"])

    # Handle missing values
    # For discounts, default missing percentage to 0.0 and code to 'NONE'
    # For returns, reason will be set if there is a return, but let's ensure order joins are handled
    
    # ==========================================
    # STEP 4: TRANSFORM
    # ==========================================
    print("Step 4: Transforming and Feature Engineering...")
    
    # Step 4a: Integrate Order Items with Products
    items_prod = order_items.merge(products, on="product_id", how="left")
    
    # Gross Revenue
    items_prod["gross_revenue"] = items_prod["quantity"] * items_prod["unit_price"]
    
    # Cost
    items_prod["cost_amount"] = items_prod["quantity"] * items_prod["cost_price"]

    # Step 4b: Merge with Orders, Discounts, Customers, Regions, Reps, and Returns
    master = items_prod.copy()
    
    # Join order details
    master = master.merge(orders, on="order_id", how="left")
    master = master.merge(customers, on="customer_id", how="left", suffixes=("", "_cust"))
    master = master.merge(regions, on="region_id", how="left")
    # Prevent region_id suffix rename by specifying suffix for rep table
    master = master.merge(reps, on="sales_rep_id", how="left", suffixes=("", "_rep"))
    
    # Merge discounts (left join)
    master = master.merge(discounts, on="order_id", how="left")
    master["discount_percentage"] = master["discount_percentage"].fillna(0.0)
    master["discount_code"] = master["discount_code"].fillna("NONE")
    
    # Merge returns (left join)
    master = master.merge(returns, on="order_id", how="left")
    master["return_reason"] = master["return_reason"].fillna("N/A")
    master["return_date"] = pd.to_datetime(master["return_date"])
    
    # Calculations at item-level
    master["discount_amount"] = master["gross_revenue"] * master["discount_percentage"]
    master["net_revenue"] = master["gross_revenue"] - master["discount_amount"]
    
    master["gross_profit"] = master["net_revenue"] - master["cost_amount"]
    master["profit_margin"] = np.where(master["net_revenue"] > 0, master["gross_profit"] / master["net_revenue"], 0.0)
    
    # --- Revenue Leakage Calculations ---
    # 1. Discount Leakage: discounts > 20% are flagged as leakage (excess discount amount)
    master["discount_leakage"] = np.where(
        master["discount_percentage"] > 0.20,
        master["gross_revenue"] * (master["discount_percentage"] - 0.20),
        0.0
    )
    
    # 2. Return Leakage: net revenue lost if order is returned
    master["return_leakage"] = np.where(
        master["order_status"] == "Returned",
        master["net_revenue"],
        0.0
    )
    
    # 3. Delay Leakage: cancelled revenue if delay > 5 days
    master["delay_leakage"] = np.where(
        (master["order_status"] == "Cancelled") & (master["delay_days"] > 5),
        master["net_revenue"],
        0.0
    )
    
    # 4. Pricing Leakage: difference between base product price and actual sold unit price before discount
    master["pricing_leakage"] = np.where(
        master["unit_price"] < master["base_price"],
        (master["base_price"] - master["unit_price"]) * master["quantity"],
        0.0
    )
    
    # Total Revenue Leakage
    master["leakage_amount"] = master["discount_leakage"] + master["return_leakage"] + master["delay_leakage"] + master["pricing_leakage"]
    master["is_leakage"] = np.where(master["leakage_amount"] > 0, 1, 0)
    master["leakage_score"] = np.where(master["net_revenue"] > 0, master["leakage_amount"] / (master["net_revenue"] + master["pricing_leakage"]), 0.0)
    
    # --- Feature Engineering ---
    # Average Order Value (AOV) will be calculated at customer segment levels.
    # Order Delay
    master["order_delay"] = master["delay_days"]
    
    # Return Rate (Boolean helper)
    master["is_returned"] = np.where(master["order_status"] == "Returned", 1, 0)
    
    # Date Parts
    master["year"] = master["order_date"].dt.year
    master["quarter"] = master["order_date"].dt.to_period("Q").astype(str)
    master["month_num"] = master["order_date"].dt.month
    master["month"] = master["order_date"].dt.strftime("%Y-%m")
    
    # Season
    def get_season(month_num):
        if month_num in [12, 1, 2]:
            return "Winter"
        elif month_num in [3, 4, 5]:
            return "Spring"
        elif month_num in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"
    master["season"] = master["month_num"].apply(get_season)
    
    # Repeat Customer Indicator (based on unique orders per customer, not items)
    unique_orders = master[["customer_id", "order_id", "order_date"]].drop_duplicates().sort_values(by=["customer_id", "order_date"])
    unique_orders["customer_order_rank"] = unique_orders.groupby("customer_id").cumcount() + 1
    order_rank_map = dict(zip(unique_orders["order_id"], unique_orders["customer_order_rank"]))
    master["customer_order_rank"] = master["order_id"].map(order_rank_map)
    master["repeat_customer_indicator"] = np.where(master["customer_order_rank"] > 1, 1, 0)


    # Customer Lifetime Value (CLV) per customer (running aggregate)
    clv_map = master.groupby("customer_id")["net_revenue"].sum().to_dict()
    master["customer_ltv"] = master["customer_id"].map(clv_map)

    # High Risk Customer
    # customer is high risk if their return rate is > 20% or average leakage score is > 25%
    cust_risk = master.groupby("customer_id").agg({
        "is_returned": "mean",
        "leakage_score": "mean"
    }).reset_index()
    cust_risk["high_risk_customer"] = np.where((cust_risk["is_returned"] > 0.20) | (cust_risk["leakage_score"] > 0.25), 1, 0)
    risk_map = dict(zip(cust_risk["customer_id"], cust_risk["high_risk_customer"]))
    master["high_risk_customer"] = master["customer_id"].map(risk_map)

    # Sort master analytical dataset back by order_date
    master = master.sort_values(by="order_date").reset_index(drop=True)
    
    # ==========================================
    # STEP 5: LOAD
    # ==========================================
    print(f"Step 5: Loading data into SQLite database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    
    # Convert datetime columns to strings before storing in SQLite
    for df_name in ["customers", "products", "regions", "reps", "orders", "order_items", "discounts", "returns", "marketing_spend", "monthly_targets"]:
        df = locals()[df_name].copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
        df.to_sql(df_name, conn, if_exists="replace", index=False)
        print(f" - Loaded raw table '{df_name}' ({len(df)} rows)")

    # Save master analytical dataset
    master_db = master.copy()
    master_db["order_date"] = master_db["order_date"].astype(str)
    master_db["shipping_date"] = master_db["shipping_date"].astype(str)
    master_db["created_date"] = master_db["created_date"].astype(str)
    if "return_date" in master_db.columns:
         master_db["return_date"] = master_db["return_date"].astype(str)
    
    master_db.to_sql("master_analytical_dataset", conn, if_exists="replace", index=False)
    print(f" - Loaded integrated master table 'master_analytical_dataset' ({len(master_db)} rows)")
    
    # Create simple views for SQL Analytics
    cursor = conn.cursor()
    cursor.execute("DROP VIEW IF EXISTS view_monthly_summary;")
    cursor.execute("""
        CREATE VIEW view_monthly_summary AS
        SELECT 
            month,
            COUNT(order_id) as total_orders,
            SUM(gross_revenue) as gross_revenue,
            SUM(discount_amount) as discount_amount,
            SUM(net_revenue) as net_revenue,
            SUM(cost_amount) as cost_amount,
            SUM(gross_profit) as gross_profit,
            AVG(profit_margin) as avg_profit_margin,
            SUM(leakage_amount) as leakage_amount
        FROM master_analytical_dataset
        GROUP BY month;
    """)
    conn.commit()
    conn.close()
    
    print("ETL Pipeline finished successfully!")
    return True

if __name__ == "__main__":
    run_etl_pipeline()
