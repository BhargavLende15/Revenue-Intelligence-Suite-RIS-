-- Top Products by Quantity and Net Revenue
WITH ProductSales AS (
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        SUM(oi.quantity) as total_quantity_sold,
        SUM(oi.quantity * oi.unit_price) as gross_product_revenue,
        SUM(oi.quantity * (oi.unit_price * (1 - COALESCE(d.discount_percentage, 0.0)))) as net_product_revenue,
        SUM(oi.quantity * (oi.unit_price * (1 - COALESCE(d.discount_percentage, 0.0)) - p.cost_price)) as product_profit
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN discounts d ON o.order_id = d.order_id
    WHERE o.order_status != 'Cancelled'
    GROUP BY p.product_id, p.product_name, p.category
)
SELECT 
    product_id,
    product_name,
    category,
    total_quantity_sold,
    ROUND(gross_product_revenue, 2) as gross_product_revenue,
    ROUND(net_product_revenue, 2) as net_product_revenue,
    ROUND(product_profit, 2) as product_profit,
    ROUND((product_profit / net_product_revenue) * 100, 2) as profit_margin_pct,
    RANK() OVER (PARTITION BY category ORDER BY net_product_revenue DESC) as category_rank
FROM ProductSales
ORDER BY net_product_revenue DESC;
