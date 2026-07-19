-- Underperforming Products: Low margin, low volume, or high return rates
WITH ProductPerformance AS (
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        COUNT(DISTINCT oi.order_id) as total_orders,
        SUM(oi.quantity) as total_qty,
        SUM(oi.quantity * (oi.unit_price * (1 - COALESCE(d.discount_percentage, 0.0)))) as net_revenue,
        SUM(oi.quantity * (oi.unit_price * (1 - COALESCE(d.discount_percentage, 0.0)) - p.cost_price)) as profit,
        SUM(CASE WHEN o.order_status = 'Returned' THEN oi.quantity ELSE 0 END) as returned_qty
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN discounts d ON o.order_id = d.order_id
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT 
    product_id,
    product_name,
    category,
    COALESCE(total_orders, 0) as total_orders,
    COALESCE(total_qty, 0) as total_qty,
    ROUND(COALESCE(net_revenue, 0.0), 2) as net_revenue,
    ROUND(COALESCE(profit, 0.0), 2) as profit,
    ROUND(COALESCE(profit / NULLIF(net_revenue, 0.0), 0.0) * 100, 2) as profit_margin_pct,
    COALESCE(returned_qty, 0) as returned_qty,
    ROUND((CAST(COALESCE(returned_qty, 0) AS FLOAT) / NULLIF(total_qty, 0)) * 100, 2) as return_rate_pct
FROM ProductPerformance
ORDER BY profit ASC, return_rate_pct DESC;
