-- Monthly Revenue Trends, Running Totals, and Month-over-Month Growth
WITH MonthlyRevenue AS (
    SELECT 
        month,
        SUM(net_revenue) as net_revenue,
        SUM(gross_profit) as profit,
        SUM(leakage_amount) as leakage
    FROM master_analytical_dataset
    WHERE order_status != 'Cancelled'
    GROUP BY month
),
LagsAndRunning AS (
    SELECT 
        month,
        net_revenue,
        profit,
        leakage,
        LAG(net_revenue, 1) OVER (ORDER BY month) as prev_month_revenue,
        SUM(net_revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total_revenue,
        SUM(profit) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total_profit
    FROM MonthlyRevenue
)
SELECT 
    month,
    ROUND(net_revenue, 2) as net_revenue,
    ROUND(profit, 2) as profit,
    ROUND(leakage, 2) as leakage,
    ROUND(running_total_revenue, 2) as running_total_revenue,
    ROUND(running_total_profit, 2) as running_total_profit,
    ROUND(COALESCE(((net_revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0.0)) * 100, 0.0), 2) as mom_growth_pct
FROM LagsAndRunning
ORDER BY month;
