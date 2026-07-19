# Revenue Intelligence Suite (RIS) - Project Guide & Portfolio Manual

This guide serves as a technical walkthrough and demonstration manual for the **Revenue Intelligence Suite (RIS)**. It is structured to help explain the architecture, data modeling, SQL queries, machine learning algorithms, and dashboard functionality during code reviews, portfolio demonstrations, and interviews.

---

## 1. Relational Database & Ingestion Schemas
RIS simulates how enterprise data exists in separate operational silos across Sales, CRM, Operations, and Marketing. In standard operations, this data is extracted, cleaned, and integrated into a single source of truth.

### The 10 Ingested Relational Datasets
1. **`customers`**: CRM account master tracking segmentations (SMB, Strategic, Enterprise) and signup timelines.
2. **`products`**: Product SKU catalog with list prices (MSRP) and cost bounds (COGS cost basis).
3. **`regions`**: Geographic territory lookup table mapping countries.
4. **`sales_representatives`**: Account executives linked to specific regions.
5. **`orders`**: Invoice bookings metadata with booking timestamps, delivery dispatch times, and channels (Direct, Online, Partner).
6. **`order_items`**: Transaction line items detailing actual billed unit prices and quantities sold per product.
7. **`discounts`**: Campaign discount codes and percentage reductions applied at the order level.
8. **`returns`**: Post-sale product refund details and check-in dates.
9. **`marketing_spend`**: Channel-level advertising expenditures (SEO, PPC, Events, Email) per territory.
10. **`monthly_targets`**: Territory-specific monthly revenue targets to evaluate target attainment.

---

## 2. The ETL Pipeline & Validation Architecture
The ETL pipeline in `etl/pipeline.py` integrates these 10 independent datasets.

```
CSV Ingestion ──> Schema Validation ──> Cleaning & Deduplication ──> Master Joins ──> SQLite Load
```

### Transformation Stages
- **Data Validation**: Checks columns presence and validates datatypes (e.g. mapping numeric fields to float/int, identifying objects/str strings).
- **Logical Cleaning**: Handles missing values (e.g. converting missing return reasons to `N/A` and missing discount percentages to `0.0`) and standardizes timestamps.
- **Relational Integrations**: Merges item-level transactions with product catalogs, customer segments, territory fields, discounts, returns, and sales reps. Suffix mappings prevent primary key collisions.
- **Operational Calculations**:
  - $NetRevenue = GrossRevenue \times (1 - DiscountPercentage)$
  - $GrossProfit = NetRevenue - COGSCostBasis$
  - $ProfitMargin = GrossProfit / NetRevenue$
- **Revenue Leakage Vectors**:
  1. *Discount Leakage*: Billed discounts exceeding a standardized corporate threshold (20%).
  2. *Return Leakage*: Total net revenue lost due to returned orders.
  3. *Delay Leakage*: Order cancellations directly attributable to logistics delays exceeding 5 days.
  4. *Pricing Leakage*: Unit selling price list discrepancy ($MSRP - BilledPrice$) prior to discount.

---

## 3. SQL Analytics CTEs & Window Queries
All queries reside in `sql/` and represent highly structured relational analytics scripts:

1. **Top Customers (`top_customers.sql`)**:
   - *Logic*: Uses a CTE to aggregate total orders, net revenue, margins, and profit per client.
   - *Relational SQL*: Employs the `RANK() OVER (ORDER BY total_net_revenue DESC)` window function to assign clean leaderboards.
2. **Top Products (`top_products.sql`)**:
   - *Logic*: Compiles gross revenue, cost, net revenue, and margin contributions per product category.
   - *Relational SQL*: Employs `RANK() OVER (PARTITION BY category ORDER BY net_product_revenue DESC)` to partition and rank top catalog performers within their respective groups (Software, Hardware, Consulting, Support).
3. **Worst Products (`worst_products.sql`)**:
   - *Logic*: Flags underperforming products with negative profit margins or elevated customer return rates.
4. **Regional Territory Review (`revenue_by_region.sql`)**:
   - *Logic*: Merges regional sales, marketing campaign spend, and monthly targets in three independent CTE tables. It calculates target achievement percentages and territory-specific **Marketing ROI** ($NetRevenue / MarketingSpend$).
5. **Running Totals (`revenue_by_month.sql`)**:
   - *Logic*: Calculates month-over-month sales growth and running totals.
   - *Relational SQL*: Uses `LAG(net_revenue, 1) OVER (ORDER BY month)` to calculate the previous month's revenue, and `SUM(net_revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` for running totals.

---

## 4. Machine Learning & Explainable AI (SHAP)
We employ 4 machine learning models (scikit-learn) and SHAP explainability to generate data-driven predictions:

### 1. Revenue Time-Series Forecast (Linear Regression)
- **Objective**: Projects monthly net revenue 6 months into the future.
- **Feature Engineering**: Generates trend indices, 1-month, 2-month, and 3-month monthly lags, and sine/cosine cyclical transformations on month numbers to capture winter/summer seasonality.
- **Confidence Intervals**: Calculates 95% confidence bands using the residuals standard error (RSE) propagating over time.

### 2. Product Demand Regressor (Random Forest)
- **Objective**: Simulates product quantity sold per order.
- **Features**: Product Category, Unit Price, Billed Discount %, Territory Region, Channel, and Month number.
- **Persona Mappings**: Standardizes categorical inputs using custom integer encoders (e.g. mapping "Software" to `0` and "Hardware" to `1`) to keep inputs clean for SHAP explainer matrix arrays.

### 3. Customer Segmenter (K-Means Clustering)
- **Objective**: Clusters customer behaviors to build persona segments.
- **Input Features**: Standardized Recency, Frequency, Monetary Value (RFM) metrics, Average Discount Percentage, and Return Rate.
- **Cluster Personas**: Standardizes features, fits K-Means, and maps cluster centroids dynamically to 4 business personas:
  - *VIP High-Value*: Frequent buyers purchasing high monetary volume with low returns.
  - *Discount Seekers*: High discount rates, low/medium monetary volumes.
  - *High Return Risk*: Elevated refund rates.
  - *Standard Customers*: Baseline balanced indicators.

### 4. Revenue Leakage Detector (Isolation Forest)
- **Objective**: Unsupervised audit analysis of operational anomalies.
- **Features**: Gross revenue, discount percentage, delivery delay days, profit margin, and return flags.
- **Logic**: Isolates billing anomalies (such as high discount rates, shipping delays, and negative margins).

### 5. Explainable AI (SHAP values)
- **Global Feature Importance**: Fits a `shap.TreeExplainer` on the Random Forest regressor and calculates the mean absolute SHAP value for each feature, identifying the strongest business drivers.
- **Local Waterfall Chart**: For any selected order, computes the SHAP force vectors (local feature contributions). A Plotly waterfall chart plots how each parameter (e.g. a 30% discount or Europe region) pushed the predicted quantity up or down relative to the baseline dataset average.

---

## 5. Dashboard User Guide

Start the app locally by running `python app.py` and navigating to `http://127.0.0.1:8050/`.

### 1. Global Interactive Filters
Located in the sidebar, these filters dynamically restrict the active dataset used by the dashboard pages:
- **Year / Region / Customer Segment / Category / Sales Channel** dropdowns update all metrics, KPI cards, and charts in real-time.
- **Enable Dark Mode**: A toggle switch that swaps stylesheet backgrounds and updates all Plotly charts with high-contrast, neon-colored curves on a dark canvas.

### 2. Tab Navigation
- **Executive Overview**: High-level scorecards (no distracting icons, but premium top-border color codes). It features MoM Growth Rate bar charts, target attainment bars, and an **AI Root-Cause Alerts Box** explaining revenue drops or spikes.
- **Revenue Analytics**: Visualizes the corporate profit margin bridge using Waterfall charts, Treemaps of regional product category share, and donut charts of channel distributions.
- **Customer Analytics**: Plots K-Means clusters on an interactive scatter chart (hover to reveal customer names) and lists the top SQL-ranked customers.
- **Product Analytics**: Displays underperforming catalog SKUs and hosts the **ML Demand Simulator Form** to test pricing and discount strategies.
- **Revenue Leakage**: Visualizes leakage categories (e.g., return leakage, discount leakage, pricing leakage) per product category and displays Isolation Forest anomaly audit logs.
- **Forecasting & SHAP**: Evaluates 6-month projected revenue bands. The dropdown selection lets you pick any order ID to render a **SHAP Waterfall Chart**, explaining how the model reached its decision.
- **Executive Report**: A printable page (`window.print`) compiling core financial tables, operational leakages, and actionable recommendations.
