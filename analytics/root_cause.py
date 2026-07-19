import pandas as pd
import numpy as np

def analyze_revenue_drop(df):
    """
    Compares the latest month's net revenue to the previous month's net revenue,
    and identifies the top contributing factor (region, category, or channel) to any drop.
    """
    monthly_sales = df.groupby("month")["net_revenue"].sum().reset_index()
    if len(monthly_sales) < 2:
        return {"status": "insufficient_data", "message": "Not enough historical data to analyze trends."}
        
    monthly_sales = monthly_sales.sort_values(by="month").reset_index(drop=True)
    latest_month = monthly_sales.iloc[-1]["month"]
    prev_month = monthly_sales.iloc[-2]["month"]
    
    latest_rev = monthly_sales.iloc[-1]["net_revenue"]
    prev_rev = monthly_sales.iloc[-2]["net_revenue"]
    
    diff = latest_rev - prev_rev
    pct_change = (diff / prev_rev) * 100
    
    if diff >= 0:
        return {
            "status": "growth",
            "message": f"Revenue grew by ${diff:,.2f} ({pct_change:.2f}%) from {prev_month} to {latest_month}.",
            "latest_month": latest_month,
            "prev_month": prev_month,
            "change_amount": diff,
            "change_pct": pct_change
        }
        
    # Analyze the drop
    # Category level breakdown
    prev_cat = df[df["month"] == prev_month].groupby("category")["net_revenue"].sum()
    latest_cat = df[df["month"] == latest_month].groupby("category")["net_revenue"].sum()
    cat_diff = (latest_cat - prev_cat).fillna(-prev_cat)
    top_dropping_cat = cat_diff.idxmin()
    cat_drop_amount = cat_diff.min()
    
    # Region level breakdown
    prev_reg = df[df["month"] == prev_month].groupby("region_name")["net_revenue"].sum()
    latest_reg = df[df["month"] == latest_month].groupby("region_name")["net_revenue"].sum()
    reg_diff = (latest_reg - prev_reg).fillna(-prev_reg)
    top_dropping_reg = reg_diff.idxmin()
    reg_drop_amount = reg_diff.min()

    # Average Discount spike check
    prev_disc = df[df["month"] == prev_month]["discount_percentage"].mean()
    latest_disc = df[df["month"] == latest_month]["discount_percentage"].mean()
    disc_spike = latest_disc - prev_disc
    
    # Return rate spike check
    prev_ret = df[df["month"] == prev_month]["is_returned"].mean()
    latest_ret = df[df["month"] == latest_month]["is_returned"].mean()
    ret_spike = latest_ret - prev_ret

    reasons = []
    reasons.append(f"Revenue declined by ${abs(diff):,.2f} (-{abs(pct_change):.2f}%) from {prev_month} to {latest_month}.")
    reasons.append(f"The product category that suffered the largest drop was '{top_dropping_cat}' with a decline of ${abs(cat_drop_amount):,.2f}.")
    reasons.append(f"Geographically, '{top_dropping_reg}' region was the hardest hit, dropping by ${abs(reg_drop_amount):,.2f}.")
    
    if disc_spike > 0.02:
        reasons.append(f"Average discounts spiked by {disc_spike*100:.1f} percentage points, contributing to compressed margins and revenue leakage.")
    if ret_spike > 0.03:
        reasons.append(f"Return rates increased by {ret_spike*100:.1f} percentage points, indicating product satisfaction or shipping delay issues.")
        
    return {
        "status": "decline",
        "message": " ".join(reasons),
        "latest_month": latest_month,
        "prev_month": prev_month,
        "change_amount": diff,
        "change_pct": pct_change,
        "top_dropping_category": top_dropping_cat,
        "category_drop_amount": cat_drop_amount,
        "top_dropping_region": top_dropping_reg,
        "region_drop_amount": reg_drop_amount,
        "discount_spike": disc_spike,
        "return_spike": ret_spike
    }

def analyze_marketing_effectiveness(df, marketing_df):
    """
    Finds regions and channels where marketing spend increased month-over-month,
    but net revenue declined (indicating ineffective marketing spend).
    """
    # Group revenue by region and month
    rev_monthly = df.groupby(["region_id", "month"])["net_revenue"].sum().reset_index()
    
    # Group marketing spend by region and month
    spend_monthly = marketing_df.groupby(["region_id", "campaign_month"])["spend_amount"].sum().reset_index()
    spend_monthly.rename(columns={"campaign_month": "month"}, inplace=True)
    
    # Merge
    merged = rev_monthly.merge(spend_monthly, on=["region_id", "month"], how="inner")
    merged = merged.sort_values(by=["region_id", "month"]).reset_index(drop=True)
    
    # Calculate MoM changes
    merged["prev_revenue"] = merged.groupby("region_id")["net_revenue"].shift(1)
    merged["prev_spend"] = merged.groupby("region_id")["spend_amount"].shift(1)
    
    merged["rev_change"] = merged["net_revenue"] - merged["prev_revenue"]
    merged["spend_change"] = merged["spend_amount"] - merged["prev_spend"]
    
    # Filter for spend increased, revenue decreased
    ineffective = merged[(merged["spend_change"] > 0) & (merged["rev_change"] < 0)].copy()
    
    results = []
    for _, row in ineffective.iterrows():
        region_id = row["region_id"]
        month = row["month"]
        results.append({
            "region_id": region_id,
            "month": month,
            "spend_increase": row["spend_change"],
            "revenue_decrease": abs(row["rev_change"]),
            "roi": row["net_revenue"] / row["spend_amount"]
        })
        
    return results

def analyze_leakage_drivers(df):
    """
    Identifies top sales representatives and channels responsible for discount leakage,
    and returns metrics for returns / shipping delay leakage.
    """
    # Discount leakage by Sales Rep
    rep_leakage = df.groupby(["sales_rep_name", "region_name"])["discount_leakage"].sum().reset_index()
    top_rep = rep_leakage.sort_values(by="discount_leakage", ascending=False).iloc[0]
    
    # Return rate reasons
    returned_orders = df[df["order_status"] == "Returned"]
    if len(returned_orders) > 0:
        top_return_reason = returned_orders["return_reason"].value_counts().idxmax()
        top_return_category = returned_orders["category"].value_counts().idxmax()
    else:
        top_return_reason = "N/A"
        top_return_category = "N/A"
        
    # Shipping delay impact
    delayed_orders = df[df["delay_days"] > 5]
    cancelled_delayed = delayed_orders[delayed_orders["order_status"] == "Cancelled"]
    delay_leakage_total = cancelled_delayed["net_revenue"].sum()
    
    return {
        "top_leakage_sales_rep": top_rep["sales_rep_name"],
        "top_leakage_rep_region": top_rep["region_name"],
        "top_leakage_rep_amount": top_rep["discount_leakage"],
        "top_return_reason": top_return_reason,
        "top_return_category": top_return_category,
        "delay_cancellation_leakage": delay_leakage_total
    }
