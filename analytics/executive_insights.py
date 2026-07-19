import pandas as pd
import numpy as np

def generate_executive_insights(df, marketing_df, targets_df):
    """
    Analyzes master data, marketing, and targets to generate dynamic executive summaries and actionable recommendations.
    """
    insights = {}
    
    # 1. Top Performing Product (by Net Revenue)
    prod_revenue = df.groupby("product_name")["net_revenue"].sum()
    if not prod_revenue.empty:
        insights["top_performing_product"] = prod_revenue.idxmax()
        insights["top_performing_product_revenue"] = float(prod_revenue.max())
    else:
        insights["top_performing_product"] = "N/A"
        insights["top_performing_product_revenue"] = 0.0

    # 2. Worst Performing Region (by Target Achievement)
    region_sales = df.groupby("region_id")["net_revenue"].sum().reset_index()
    region_targets = targets_df.groupby("region_id")["target_revenue"].sum().reset_index()
    reg_perf = region_sales.merge(region_targets, on="region_id")
    reg_perf["achievement"] = reg_perf["net_revenue"] / reg_perf["target_revenue"]
    
    regions_map = dict(zip(df["region_id"], df["region_name"]))
    
    if not reg_perf.empty:
        worst_reg_id = reg_perf.sort_values(by="achievement").iloc[0]["region_id"]
        insights["worst_performing_region"] = regions_map.get(worst_reg_id, worst_reg_id)
        insights["worst_performing_region_achievement"] = float(reg_perf["achievement"].min())
    else:
        insights["worst_performing_region"] = "N/A"
        insights["worst_performing_region_achievement"] = 0.0

    # 3. Highest Value Customer
    cust_revenue = df.groupby("customer_name")["net_revenue"].sum()
    if not cust_revenue.empty:
        insights["highest_value_customer"] = cust_revenue.idxmax()
        insights["highest_value_customer_revenue"] = float(cust_revenue.max())
    else:
        insights["highest_value_customer"] = "N/A"
        insights["highest_value_customer_revenue"] = 0.0

    # 4. Most Returned Category (by Quantity returned)
    returned_items = df[df["order_status"] == "Returned"]
    cat_returns = returned_items.groupby("category")["quantity"].sum()
    if not cat_returns.empty:
        insights["most_returned_category"] = cat_returns.idxmax()
        insights["most_returned_category_qty"] = int(cat_returns.max())
    else:
        insights["most_returned_category"] = "N/A"
        insights["most_returned_category_qty"] = 0

    # 5. Highest Leakage Category
    cat_leakage = df.groupby("category")["leakage_amount"].sum()
    if not cat_leakage.empty:
        insights["highest_leakage_category"] = cat_leakage.idxmax()
        insights["highest_leakage_category_amount"] = float(cat_leakage.max())
    else:
        insights["highest_leakage_category"] = "N/A"
        insights["highest_leakage_category_amount"] = 0.0

    # 6. Fastest Growing Region (comparing first half vs second half of dates)
    df["order_date"] = pd.to_datetime(df["order_date"])
    min_date = df["order_date"].min()
    max_date = df["order_date"].max()
    midpoint = min_date + (max_date - min_date) / 2
    
    first_half = df[df["order_date"] < midpoint]
    second_half = df[df["order_date"] >= midpoint]
    
    fh_rev = first_half.groupby("region_name")["net_revenue"].sum()
    sh_rev = second_half.groupby("region_name")["net_revenue"].sum()
    
    growth = ((sh_rev - fh_rev) / fh_rev).dropna()
    if not growth.empty:
        insights["fastest_growing_region"] = growth.idxmax()
        insights["fastest_growing_region_growth"] = float(growth.max())
    else:
        insights["fastest_growing_region"] = "N/A"
        insights["fastest_growing_region_growth"] = 0.0

    # 7. Total Leakage summary
    total_net = float(df["net_revenue"].sum())
    total_leakage = float(df["leakage_amount"].sum())
    insights["total_net_revenue"] = total_net
    insights["total_leakage"] = total_leakage
    insights["overall_leakage_rate"] = total_leakage / (total_net + df["pricing_leakage"].sum()) if total_net > 0 else 0.0

    # 8. Actionable Business Recommendations (Data-Driven)
    recommendations = []
    
    # Check 8a: High discount leakage reps
    rep_leak = df.groupby("sales_rep_name")["discount_leakage"].sum().reset_index()
    if not rep_leak.empty:
        top_rep_leak = rep_leak.sort_values(by="discount_leakage", ascending=False).iloc[0]
        if top_rep_leak["discount_leakage"] > 5000:
            recommendations.append({
                "action": f"Establish strict discount approval workflows for {top_rep_leak['sales_rep_name']}.",
                "rationale": f"Representative generated the highest discount leakage of ${top_rep_leak['discount_leakage']:,.2f}.",
                "impact": "High"
            })
            
    # Check 8b: Regional delivery delay leakage
    reg_delay_leak = df.groupby("region_name").agg({
        "delay_days": "mean",
        "delay_leakage": "sum"
    }).reset_index()
    if not reg_delay_leak.empty:
        top_delay_leak = reg_delay_leak.sort_values(by="delay_leakage", ascending=False).iloc[0]
        if top_delay_leak["delay_leakage"] > 2000:
            recommendations.append({
                "action": f"Audit delivery logistics and shipping partners in {top_delay_leak['region_name']}.",
                "rationale": f"High shipping delays (avg {top_delay_leak['delay_days']:.1f} days) triggered order cancellations leading to ${top_delay_leak['delay_leakage']:,.2f} in lost revenue.",
                "impact": "High"
            })
            
    # Check 8c: Return rate
    returned_orders = df[df["order_status"] == "Returned"]
    if len(returned_orders) > 0:
        cat_ret_rate = (returned_orders.groupby("category")["order_id"].count() / df.groupby("category")["order_id"].count()).dropna()
        if not cat_ret_rate.empty and cat_ret_rate.max() > 0.08:
            top_ret_cat = cat_ret_rate.idxmax()
            recommendations.append({
                "action": f"Initiate quality assurance review for '{top_ret_cat}' category.",
                "rationale": f"This category exhibits a return rate of {cat_ret_rate.max()*100:.1f}%, which is significantly higher than the baseline.",
                "impact": "Medium"
            })

    # Check 8d: PPC marketing spend efficiency
    from analytics.root_cause import analyze_marketing_effectiveness
    ineffective = analyze_marketing_effectiveness(df, marketing_df)
    if ineffective:
        worst_mkt = sorted(ineffective, key=lambda x: x["revenue_decrease"], reverse=True)[0]
        worst_reg_name = regions_map.get(worst_mkt["region_id"], worst_mkt["region_id"])
        recommendations.append({
            "action": f"Reallocate marketing budget away from PPC in {worst_reg_name}.",
            "rationale": f"Marketing spend increased but revenue declined in {worst_mkt['month']}, yielding a poor ROI of {worst_mkt['roi']:.2f}.",
            "impact": "Medium"
        })
        
    # Default fallback recommendation
    if not recommendations:
        recommendations.append({
            "action": "Implement standard price audits across all sales channels.",
            "rationale": "Maintain consistency between base prices and customer invoices.",
            "impact": "Low"
        })
        
    insights["recommendations"] = recommendations
    return insights
