-- Revenue Leakage by Product Category and Sales Channel
SELECT 
    category,
    sales_channel,
    COUNT(order_id) as total_orders,
    ROUND(SUM(net_revenue), 2) as total_net_revenue,
    ROUND(SUM(discount_leakage), 2) as discount_leakage,
    ROUND(SUM(return_leakage), 2) as return_leakage,
    ROUND(SUM(delay_leakage), 2) as delay_leakage,
    ROUND(SUM(pricing_leakage), 2) as pricing_leakage,
    ROUND(SUM(leakage_amount), 2) as total_leakage,
    ROUND((SUM(leakage_amount) / NULLIF(SUM(net_revenue) + SUM(pricing_leakage), 0.0)) * 100, 2) as leakage_rate_pct
FROM master_analytical_dataset
GROUP BY category, sales_channel
ORDER BY total_leakage DESC;
