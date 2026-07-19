-- Regional Revenue and Profit Summary with Marketing ROI and Target Attainment
WITH RegionalSales AS (
    SELECT 
        region_id,
        region_name,
        country,
        COUNT(DISTINCT order_id) as total_orders,
        SUM(net_revenue) as total_net_revenue,
        SUM(gross_profit) as total_profit,
        SUM(leakage_amount) as total_leakage
    FROM master_analytical_dataset
    WHERE order_status != 'Cancelled'
    GROUP BY region_id, region_name, country
),
RegionalSpend AS (
    SELECT 
        region_id,
        SUM(spend_amount) as total_marketing_spend
    FROM marketing_spend
    GROUP BY region_id
),
RegionalTargets AS (
    SELECT 
        region_id,
        SUM(target_revenue) as total_target_revenue
    FROM monthly_targets
    GROUP BY region_id
)
SELECT 
    rs.region_id,
    rs.region_name,
    rs.country,
    rs.total_orders,
    ROUND(rs.total_net_revenue, 2) as total_net_revenue,
    ROUND(rs.total_profit, 2) as total_profit,
    ROUND((rs.total_profit / rs.total_net_revenue) * 100, 2) as profit_margin_pct,
    ROUND(rs.total_leakage, 2) as total_leakage,
    ROUND(COALESCE(sp.total_marketing_spend, 0.0), 2) as total_marketing_spend,
    ROUND(COALESCE(rs.total_net_revenue / NULLIF(sp.total_marketing_spend, 0.0), 0.0), 2) as marketing_roi,
    ROUND(COALESCE(tg.total_target_revenue, 0.0), 2) as total_target_revenue,
    ROUND((rs.total_net_revenue / NULLIF(tg.total_target_revenue, 0.0)) * 100, 2) as target_achievement_pct
FROM RegionalSales rs
LEFT JOIN RegionalSpend sp ON rs.region_id = sp.region_id
LEFT JOIN RegionalTargets tg ON rs.region_id = tg.region_id
ORDER BY total_net_revenue DESC;
