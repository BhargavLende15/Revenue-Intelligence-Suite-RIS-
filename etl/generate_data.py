import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_enterprise_data():
    print("Generating simulated raw enterprise data...")
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # 1. Regions
    regions = [
        {"region_id": "REG01", "region_name": "North America", "country": "United States"},
        {"region_id": "REG02", "region_name": "Europe", "country": "United Kingdom"},
        {"region_id": "REG03", "region_name": "Asia-Pacific", "country": "Japan"},
        {"region_id": "REG04", "region_name": "Latin America", "country": "Brazil"}
    ]
    df_regions = pd.DataFrame(regions)
    df_regions.to_csv(f"{raw_dir}/regions.csv", index=False)

    # 2. Sales Representatives (2 per region)
    reps = [
        {"sales_rep_id": "REP01", "sales_rep_name": "Alice Smith", "region_id": "REG01"},
        {"sales_rep_id": "REP02", "sales_rep_name": "Bob Johnson", "region_id": "REG01"},
        {"sales_rep_id": "REP03", "sales_rep_name": "Charlie Brown", "region_id": "REG02"},
        {"sales_rep_id": "REP04", "sales_rep_name": "Diana Prince", "region_id": "REG02"},
        {"sales_rep_id": "REP05", "sales_rep_name": "Ethan Hunt", "region_id": "REG03"},
        {"sales_rep_id": "REP06", "sales_rep_name": "Fiona Gallagher", "region_id": "REG03"},
        {"sales_rep_id": "REP07", "sales_rep_name": "George Clooney", "region_id": "REG04"},
        {"sales_rep_id": "REP08", "sales_rep_name": "Hannah Abbott", "region_id": "REG04"}
    ]
    df_reps = pd.DataFrame(reps)
    df_reps.to_csv(f"{raw_dir}/sales_representatives.csv", index=False)

    # 3. Products (15 products across 4 categories)
    products = [
        {"product_id": "PROD001", "product_name": "RIS Enterprise Core License", "category": "Software", "base_price": 5000.0, "cost_price": 1000.0},
        {"product_id": "PROD002", "product_name": "RIS Cloud Connector Pro", "category": "Software", "base_price": 1200.0, "cost_price": 300.0},
        {"product_id": "PROD003", "product_name": "RIS Analytics Plug-in", "category": "Software", "base_price": 800.0, "cost_price": 150.0},
        {"product_id": "PROD004", "product_name": "RIS Team Sync License", "category": "Software", "base_price": 450.0, "cost_price": 90.0},
        
        {"product_id": "PROD005", "product_name": "RIS Edge Processing Gateway", "category": "Hardware", "base_price": 1500.0, "cost_price": 950.0},
        {"product_id": "PROD006", "product_name": "RIS Server Rack Appliance", "category": "Hardware", "base_price": 8500.0, "cost_price": 5800.0},
        {"product_id": "PROD007", "product_name": "RIS IoT Smart Sensor", "category": "Hardware", "base_price": 120.0, "cost_price": 65.0},
        {"product_id": "PROD008", "product_name": "RIS Backup Storage Unit", "category": "Hardware", "base_price": 2200.0, "cost_price": 1400.0},
        
        {"product_id": "PROD009", "product_name": "Enterprise Architecture Audit", "category": "Consulting", "base_price": 3500.0, "cost_price": 2000.0},
        {"product_id": "PROD010", "product_name": "Custom Integration Workshop", "category": "Consulting", "base_price": 2500.0, "cost_price": 1500.0},
        {"product_id": "PROD011", "product_name": "Executive Strategy Session", "category": "Consulting", "base_price": 6000.0, "cost_price": 3200.0},
        
        {"product_id": "PROD012", "product_name": "24/7 Platinum Phone Support", "category": "Support", "base_price": 1200.0, "cost_price": 500.0},
        {"product_id": "PROD013", "product_name": "Gold Business-Hour Support", "category": "Support", "base_price": 600.0, "cost_price": 250.0},
        {"product_id": "PROD014", "product_name": "Silver Email Support Plan", "category": "Support", "base_price": 300.0, "cost_price": 120.0},
        {"product_id": "PROD015", "product_name": "Dedicated Support Account Rep", "category": "Support", "base_price": 4000.0, "cost_price": 2200.0}
    ]
    df_products = pd.DataFrame(products)
    df_products.to_csv(f"{raw_dir}/products.csv", index=False)

    # 4. Customers (100 customers)
    segments = ["SMB", "Strategic", "Enterprise"]
    segment_weights = [0.5, 0.3, 0.2]
    
    first_names = ["Apex", "Vertex", "Quantum", "Nexus", "Stellar", "Core", "Global", "Nova", "Alpha", "Zenith", 
                   "Pinnacle", "Aegis", "Vanguard", "Summit", "Matrix", "Echo", "Infinity", "Prism", "Beacon", "Legacy"]
    second_names = ["Solutions", "Systems", "Technologies", "Corp", "Industries", "Group", "Partners", "Logistics", "Services", "Ventures"]

    customers = []
    start_date = datetime(2024, 1, 1)
    for i in range(1, 101):
        cust_id = f"CUST{i:03d}"
        cust_name = f"{random.choice(first_names)} {random.choice(second_names)}"
        cust_segment = random.choices(segments, weights=segment_weights)[0]
        cust_created = start_date + timedelta(days=random.randint(0, 500))
        customers.append({
            "customer_id": cust_id,
            "customer_name": cust_name,
            "customer_segment": cust_segment,
            "created_date": cust_created.strftime("%Y-%m-%d")
        })
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv(f"{raw_dir}/customers.csv", index=False)

    # 5. Orders (approx 1200 orders spread over 24 months: 2024-07 to 2026-06)
    orders = []
    order_id_counter = 1
    start_sales_date = datetime(2024, 7, 1)
    
    # We will simulate seasonal patterns (higher sales in Q4, lower sales in Jan/Jul)
    # And we will simulate a general upward growth trend.
    channels = ["Direct", "Online", "Partner"]
    channel_weights = [0.4, 0.4, 0.2]
    
    statuses = ["Completed", "Returned", "Cancelled"]
    status_weights = [0.88, 0.08, 0.04] # baseline rates

    # Map customers to lists for easier selection based on segments
    cust_by_seg = {seg: df_customers[df_customers["customer_segment"] == seg]["customer_id"].tolist() for seg in segments}

    num_days = (datetime(2026, 6, 30) - start_sales_date).days
    
    # Daily loop to generate random orders with trend/seasonality
    for day in range(num_days):
        current_date = start_sales_date + timedelta(days=day)
        month = current_date.month
        year = current_date.year
        
        # Seasonality factor: Q4 (Oct, Nov, Dec) has higher sales volume. Jan and Jul have slightly lower sales.
        seasonality = 1.0
        if month in [10, 11, 12]:
            seasonality = 1.4
        elif month in [1, 7]:
            seasonality = 0.8
            
        # Growth factor: sales increase over time (simulated up to 1.5x by the end of 2 years)
        growth = 1.0 + (day / num_days) * 0.5
        
        # Base expected orders per day
        base_orders = 1.6
        num_orders_today = np.random.poisson(base_orders * seasonality * growth)
        
        for _ in range(num_orders_today):
            order_id = f"ORD{order_id_counter:04d}"
            
            # Select random sales rep, which defines the region
            rep_row = random.choice(reps)
            rep_id = rep_row["sales_rep_id"]
            region_id = rep_row["region_id"]
            
            # Select customer segment, then customer
            seg = random.choices(segments, weights=segment_weights)[0]
            cust_id = random.choice(cust_by_seg[seg])
            
            # Channel
            channel = random.choices(channels, weights=channel_weights)[0]
            
            # Order status (we will adjust status weight for specific conditions to inject leakages later)
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Shipping delay: Standard is 1-4 days. 
            # Leakage simulation: George Clooney (REP07) and Hannah Abbott (REP08) in Latin America (REG04)
            # have logistic issues, leading to higher shipping delays (5-12 days).
            if region_id == "REG04":
                delay_days = random.choices([1, 2, 3, 4, 5, 7, 9, 11, 14], weights=[0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0.15, 0.1, 0.05])[0]
            else:
                delay_days = random.choices([1, 2, 3, 4, 5, 7], weights=[0.3, 0.4, 0.15, 0.08, 0.05, 0.02])[0]
                
            shipping_date = current_date + timedelta(days=delay_days)
            
            # If delay is > 5 days, returns and cancellations spike
            if delay_days > 5:
                # Override status to Return or Cancel with higher probability
                status = random.choices(["Completed", "Returned", "Cancelled"], weights=[0.4, 0.4, 0.2])[0]
                
            orders.append({
                "order_id": order_id,
                "customer_id": cust_id,
                "sales_rep_id": rep_id,
                "region_id": region_id,
                "order_date": current_date.strftime("%Y-%m-%d"),
                "shipping_date": shipping_date.strftime("%Y-%m-%d"),
                "order_status": status,
                "sales_channel": channel,
                "delay_days": delay_days
            })
            order_id_counter += 1

    df_orders = pd.DataFrame(orders)
    df_orders.to_csv(f"{raw_dir}/orders.csv", index=False)

    # 6. Order Items (1 to 4 items per order)
    order_items = []
    item_id_counter = 1
    
    for _, order in df_orders.iterrows():
        order_id = order["order_id"]
        customer_id = order["customer_id"]
        
        # Get customer segment
        cust_seg = df_customers[df_customers["customer_id"] == customer_id]["customer_segment"].values[0]
        
        # Enterprise buys larger quantities and more software/hardware.
        # SMB buys smaller quantities and mostly support/software.
        num_items = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        
        # Sample products
        selected_prod_ids = random.sample([p["product_id"] for p in products], num_items)
        
        for prod_id in selected_prod_ids:
            prod_info = next(p for p in products if p["product_id"] == prod_id)
            
            if cust_seg == "Enterprise":
                quantity = random.randint(5, 20)
            elif cust_seg == "Strategic":
                quantity = random.randint(2, 8)
            else: # SMB
                quantity = random.randint(1, 3)
                
            # Base price
            unit_price = prod_info["base_price"]
            
            # Introduce price discrepancies: some random products sold at list price mismatch (revenue leakage)
            # E.g., a pricing error: unit price is set below cost price or base price by 10-25%
            if random.random() < 0.04:
                # 4% price discrepancy leakage
                unit_price = round(prod_info["base_price"] * random.uniform(0.7, 0.9), 2)
            
            order_items.append({
                "order_item_id": f"ITEM{item_id_counter:05d}",
                "order_id": order_id,
                "product_id": prod_id,
                "quantity": quantity,
                "unit_price": unit_price
            })
            item_id_counter += 1
            
    df_items = pd.DataFrame(order_items)
    df_items.to_csv(f"{raw_dir}/order_items.csv", index=False)

    # 7. Discounts (not all orders get discounts. Let's make it linked to orders)
    # Leakage Simulation: Sales rep Ethan Hunt (REP05) and George Clooney (REP07) frequently offer
    # massive, unauthorized discounts (30% to 50%) to close deals, hurting profit margins.
    discounts = []
    discount_id_counter = 1
    
    for _, order in df_orders.iterrows():
        order_id = order["order_id"]
        rep_id = order["sales_rep_id"]
        
        # Decide if discount is given
        has_discount = random.random() < 0.35 # 35% standard discount rate
        
        # Ethan Hunt (REP05) and George Clooney (REP07) give discounts 65% of the time
        if rep_id in ["REP05", "REP07"]:
            has_discount = random.random() < 0.65
            
        if has_discount:
            if rep_id in ["REP05", "REP07"]:
                # High discount leakage
                discount_percentage = random.choices([0.2, 0.25, 0.3, 0.4, 0.5], weights=[0.2, 0.2, 0.3, 0.2, 0.1])[0]
                discount_code = f"REP_AUTH_{int(discount_percentage*100)}"
            else:
                # Standard discounts
                discount_percentage = random.choices([0.05, 0.1, 0.15, 0.2], weights=[0.4, 0.3, 0.2, 0.1])[0]
                discount_code = f"PROMO{int(discount_percentage*100)}"
                
            discounts.append({
                "discount_id": f"DSC{discount_id_counter:04d}",
                "order_id": order_id,
                "discount_percentage": discount_percentage,
                "discount_code": discount_code
            })
            discount_id_counter += 1
            
    df_discounts = pd.DataFrame(discounts)
    df_discounts.to_csv(f"{raw_dir}/discounts.csv", index=False)

    # 8. Returns (linked only to Returned orders)
    returns = []
    return_id_counter = 1
    
    returned_orders = df_orders[df_orders["order_status"] == "Returned"]
    for _, order in returned_orders.iterrows():
        order_id = order["order_id"]
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
        delay_days = order["delay_days"]
        
        # Return date is order_date + shipping_delay + 2 to 10 days
        return_date = order_date + timedelta(days=int(delay_days) + random.randint(2, 10))
        
        # If shipping delay is long, reason is mostly "Late Delivery"
        if delay_days > 5:
            reason = random.choices(["Late Delivery", "Wrong Item", "Unsatisfied"], weights=[0.7, 0.15, 0.15])[0]
        else:
            reason = random.choice(["Defective", "Wrong Item", "Unsatisfied"])
            
        returns.append({
            "return_id": f"RET{return_id_counter:03d}",
            "order_id": order_id,
            "return_date": return_date.strftime("%Y-%m-%d"),
            "return_reason": reason
        })
        return_id_counter += 1
        
    df_returns = pd.DataFrame(returns)
    df_returns.to_csv(f"{raw_dir}/returns.csv", index=False)

    # 9. Marketing Spend (Monthly spend per region per channel)
    marketing_channels = ["SEO", "PPC", "Events", "Email"]
    marketing_spend = []
    spend_id_counter = 1
    
    # 24 months list
    months_list = []
    curr = datetime(2024, 7, 1)
    while curr <= datetime(2026, 6, 30):
        months_list.append(curr.strftime("%Y-%m"))
        # Move to next month
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
            
    for m in months_list:
        for r in df_regions["region_id"]:
            # Baseline spend amounts
            for chan in marketing_channels:
                base_spend = 1500.0
                if r == "REG01": # North America spends more
                    base_spend = 3000.0
                elif r == "REG02": # Europe spends mid
                    base_spend = 2000.0
                    
                # Seasonal adjustments (spend more in Q4)
                m_int = int(m.split("-")[1])
                seasonal_multiplier = 1.3 if m_int in [10, 11, 12] else 1.0
                
                # Ineffective marketing spend simulation:
                # REG04 (Latin America) PPC spending spikes enormously in Q1 2026, 
                # but sales growth does NOT follow, indicating ineffective spend.
                if r == "REG04" and chan == "PPC" and m in ["2026-01", "2026-02", "2026-03"]:
                    spend_amount = round(base_spend * 4.5 * random.uniform(0.9, 1.1), 2) # Spike spend by 4.5x
                else:
                    spend_amount = round(base_spend * seasonal_multiplier * random.uniform(0.8, 1.2), 2)
                    
                marketing_spend.append({
                    "spend_id": f"MKT{spend_id_counter:04d}",
                    "region_id": r,
                    "campaign_month": m,
                    "marketing_channel": chan,
                    "spend_amount": spend_amount
                })
                spend_id_counter += 1
                
    df_marketing = pd.DataFrame(marketing_spend)
    df_marketing.to_csv(f"{raw_dir}/marketing_spend.csv", index=False)

    # 10. Monthly Targets (per region per month)
    monthly_targets = []
    target_id_counter = 1
    
    for m in months_list:
        m_int = int(m.split("-")[1])
        for r in df_regions["region_id"]:
            # Targets increase month over month representing growth target
            # REG01: $60k-$120k
            # REG02: $40k-$85k
            # REG03: $30k-$60k
            # REG04: $15k-$35k
            month_idx = months_list.index(m)
            
            if r == "REG01":
                base_tgt = 60000 + (month_idx * 2500)
            elif r == "REG02":
                base_tgt = 40000 + (month_idx * 1800)
            elif r == "REG03":
                base_tgt = 30000 + (month_idx * 1200)
            else: # REG04
                base_tgt = 15000 + (month_idx * 800)
                
            # Seasonality on targets
            if m_int in [11, 12]:
                base_tgt *= 1.25 # increase target in peak months
                
            monthly_targets.append({
                "target_id": f"TGT{target_id_counter:03d}",
                "region_id": r,
                "target_month": m,
                "target_revenue": round(base_tgt, 2)
            })
            target_id_counter += 1
            
    df_targets = pd.DataFrame(monthly_targets)
    df_targets.to_csv(f"{raw_dir}/monthly_targets.csv", index=False)

    print("Successfully generated all 10 raw datasets under data/raw/")

if __name__ == "__main__":
    generate_enterprise_data()
