import dash
from dash import dcc, html, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from analytics.sql_executor import run_raw_query, execute_sql_query
from utils.helpers import get_theme_colors, apply_plotly_theme, filter_dataframe, create_kpi_card
from models.segmentation import CustomerSegmenter

dash.register_page(__name__, path="/customers")

def layout():
    return dbc.Container([
        # Page Title Row
        dbc.Row([
            dbc.Col([
                html.H2("Customer Analytics & ML Segmentation", className="mb-0", style={"fontWeight": "700"}),
                html.P("Customer value mapping, K-Means clustering, and high-value customer analytics.", className="text-muted", style={"fontSize": "14px"})
            ], width=12)
        ], className="mb-4"),
        
        # Mini KPI Row
        dbc.Row([
            dbc.Col(id="cust-kpi-count", width=12, md=4, className="mb-3"),
            dbc.Col(id="cust-kpi-clv", width=12, md=4, className="mb-3"),
            dbc.Col(id="cust-kpi-repeat", width=12, md=4, className="mb-3"),
        ], className="mb-4"),
        
        # Row for Clusters Scatter & CLV Distribution
        dbc.Row([
            # K-Means Clusters Plot
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Customer Persona Clusters (K-Means)", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="customer-clusters-plot", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=7, className="mb-4"),
            
            # CLV Histogram/Box Plot
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Customer Lifetime Value (LTV) Distribution", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="clv-dist-plot", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=5, className="mb-4")
        ]),
        
        # Top Customers Table Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Top Ranked Customers (SQL Window Query)", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        html.Div(id="top-customers-table-container")
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, className="mb-4")
        ])
    ], fluid=True)

@callback(
    [
        Output("cust-kpi-count", "children"),
        Output("cust-kpi-clv", "children"),
        Output("cust-kpi-repeat", "children"),
        Output("customer-clusters-plot", "figure"),
        Output("clv-dist-plot", "figure"),
        Output("top-customers-table-container", "children")
    ],
    [
        Input("store-filters", "data"),
        Input("store-theme", "data")
    ]
)
def update_customer_analytics(filters, theme_data):
    dark_mode = theme_data.get("dark_mode", False) if theme_data else False
    theme = get_theme_colors(dark_mode)
    
    # 1. Load Data
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    
    # 2. Filter data
    filtered_df = filter_dataframe(df, filters)
    
    # 3. Calculate metrics
    num_cust = filtered_df["customer_id"].nunique()
    
    # Total net revenue per customer
    cust_totals = filtered_df.groupby("customer_id")["net_revenue"].sum()
    avg_clv = cust_totals.mean() if not cust_totals.empty else 0.0
    
    # Repeat rate
    repeat_cust_count = filtered_df[filtered_df["repeat_customer_indicator"] == 1]["customer_id"].nunique()
    repeat_rate = (repeat_cust_count / num_cust * 100) if num_cust > 0 else 0.0
    
    card_count = create_kpi_card("Active Clients", f"{num_cust:,}", theme["primary"], "Filtered customer count", dark_mode)
    card_clv = create_kpi_card("Avg LTV", f"${avg_clv:,.2f}", theme["success"], "Average customer lifetime value", dark_mode)
    card_repeat = create_kpi_card("Repeat Buyer Rate", f"{repeat_rate:.1f}%", theme["warning"], f"{repeat_cust_count} repeat buyers", dark_mode)

    # 4. K-Means Customer Clustering Visualization
    # Run the model segmenter on the full dataset to get segments, then filter the resulting segment dataframe
    segmenter = CustomerSegmenter()
    # Check if models/saved/segmenter.pkl exists
    if segmenter.load_model():
        clustered_data = segmenter.build_rfm_features(df)
        X_scaled = segmenter.scaler.transform(clustered_data[["recency", "frequency", "monetary", "discount_percentage", "is_returned"]])
        clustered_data["cluster"] = segmenter.kmeans.predict(X_scaled)
        clustered_data["segment_name"] = clustered_data["cluster"].map(segmenter.cluster_names)
    else:
        # Train and save on the fly
        clustered_data = segmenter.train(df)
        
    # Apply filter logic (by segment name / region / year if mapped)
    # Map customer_segment (SMB, strategic) and region
    # To keep filter matching correct, filter clustered_data by customer IDs in filtered_df
    filtered_cust_ids = filtered_df["customer_id"].unique()
    clustered_filtered = clustered_data[clustered_data["customer_id"].isin(filtered_cust_ids)].copy()
    
    if clustered_filtered.empty:
        # Fallback if no matching customer segment
        clustered_filtered = clustered_data.copy()
        
    colors_map = {
        "VIP High-Value": theme["success"],
        "Discount Seekers": theme["warning"],
        "High Return Risk": theme["danger"],
        "Standard Customers": theme["primary"]
    }
    
    fig_scatter = px.scatter(
        clustered_filtered, x="frequency", y="monetary", color="segment_name",
        color_discrete_map=colors_map,
        size="frequency",
        hover_data=["customer_name", "recency", "discount_percentage", "is_returned"],
        labels={
            "frequency": "Order Frequency (Count)",
            "monetary": "Lifetime Monetary Value ($)",
            "segment_name": "Cluster Persona"
        }
    )
    fig_scatter.update_layout(
        title=dict(text="K-Means Clusters: Purchase Frequency vs Lifetime Value", font=dict(size=14)),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_scatter, dark_mode)

    # 5. CLV Distribution Plot (Histogram)
    fig_dist = px.histogram(
        clustered_filtered, x="monetary", 
        nbins=20,
        color_discrete_sequence=[theme["accent"]],
        labels={"monetary": "Lifetime Value ($)"}
    )
    fig_dist.update_layout(
        title=dict(text="Distribution of Lifetime Monetary Value", font=dict(size=14)),
        yaxis_title="Number of Customers",
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_dist, dark_mode)

    # 6. Top Ranked Customers Table
    # We execute our top_customers SQL query!
    # Note: top_customers.sql ranks all customers based on master_analytical_dataset.
    # To support dynamic filters in SQL, we can either write a modified SQL or query from DB and filter in pandas.
    # Using execute_sql_query returns the full ranked list. Let's filter it in pandas by customer IDs in filtered_df.
    top_cust_df = execute_sql_query("top_customers")
    top_cust_filtered = top_cust_df[top_cust_df["customer_id"].isin(filtered_cust_ids)].copy()
    
    # Recalculate rank based on filtered subset
    top_cust_filtered["revenue_rank"] = range(1, len(top_cust_filtered) + 1)
    
    # Convert numbers to strings for representation
    table_data = top_cust_filtered.head(10).to_dict("records")
    
    # Setup Bootstrap table
    table_header = [
        html.Thead(html.Tr([
            html.Th("Rank"),
            html.Th("Customer ID"),
            html.Th("Customer Name"),
            html.Th("Segment"),
            html.Th("Total Orders"),
            html.Th("Net Sales ($)"),
            html.Th("Total Profit ($)"),
            html.Th("Avg Margin (%)"),
        ]))
    ]
    
    table_rows = []
    for r in table_data:
        table_rows.append(html.Tr([
            html.Td(r["revenue_rank"], style={"fontWeight": "bold"}),
            html.Td(r["customer_id"]),
            html.Td(r["customer_name"]),
            html.Td(r["customer_segment"]),
            html.Td(f"{r['total_orders']:,}"),
            html.Td(f"${r['total_net_revenue']:,.2f}"),
            html.Td(f"${r['total_profit']:,.2f}"),
            html.Td(f"{r['avg_profit_margin_pct']:.1f}%"),
        ]))
        
    table_body = [html.Tbody(table_rows)]
    
    bootstrap_table = dbc.Table(
        table_header + table_body,
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        style={"color": theme["text"], "backgroundColor": theme["card_bg"], "borderColor": theme["grid"], "fontSize": "13px"}
    )
    
    return card_count, card_clv, card_repeat, fig_scatter, fig_dist, bootstrap_table
