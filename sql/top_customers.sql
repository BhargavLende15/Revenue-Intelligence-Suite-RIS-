-- Top Customers by Net Revenue, Orders, and Average Margin
WITH CustomerMetrics AS (
    SELECT 
        customer_id,
        customer_name,
        customer_segment,
        COUNT(DISTINCT order_id) as total_orders,
        SUM(net_revenue) as total_net_revenue,
        SUM(gross_profit) as total_profit,
        AVG(profit_margin) as avg_profit_margin
    FROM master_analytical_dataset
    WHERE order_status != 'Cancelled'
    GROUP BY customer_id, customer_name, customer_segment
)
SELECT 
    customer_id,
    customer_name,
    customer_segment,
    total_orders,
    ROUND(total_net_revenue, 2) as total_net_revenue,
    ROUND(total_profit, 2) as total_profit,
    ROUND(avg_profit_margin * 100, 2) as avg_profit_margin_pct,
    RANK() OVER (ORDER BY total_net_revenue DESC) as revenue_rank
FROM CustomerMetrics
ORDER BY total_net_revenue DESC;
