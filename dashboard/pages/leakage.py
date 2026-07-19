import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from analytics.sql_executor import run_raw_query
from utils.helpers import get_theme_colors, apply_plotly_theme, filter_dataframe, create_kpi_card
from models.leakage_detector import LeakageAnomalyDetector

dash.register_page(__name__, path="/leakage")

def layout():
    return dbc.Container([
        # Page Title Row
        dbc.Row([
            dbc.Col([
                html.H2("Revenue Leakage & Audit Analytics", className="mb-0", style={"fontWeight": "700"}),
                html.P("Detect anomalies, monitor returns, and identify leakage drivers using Isolation Forest.", className="text-muted", style={"fontSize": "14px"})
            ], width=12)
        ], className="mb-4"),
        
        # Row 1: KPI Cards (No Icons)
        dbc.Row([
            dbc.Col(id="leak-kpi-total", width=12, md=4, className="mb-3"),
            dbc.Col(id="leak-kpi-rate", width=12, md=4, className="mb-3"),
            dbc.Col(id="leak-kpi-anomalies", width=12, md=4, className="mb-3"),
        ], className="mb-4"),
        
        # Row 2: Isolation Forest Anomaly Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.I(className="fas fa-search me-2", style={"color": "#DC3545"}),
                            html.H5("Audited Pricing & Logistics Anomalies (Isolation Forest Outliers)", className="d-inline mb-0", style={"fontSize": "16px", "fontWeight": "600"})
                        ])
                    ),
                    dbc.CardBody([
                        html.Div(id="anomaly-table-container", style={"maxHeight": "300px", "overflowY": "auto"})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, className="mb-4")
        ]),
        
        # Row 3: Leakage Breakdown Chart (NEW VISUAL)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Revenue Leakage Breakdown by Category & Cause", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="leakage-cat-bar", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, className="mb-4")
        ]),
        
        # Row 4: Return reasons & Delay Return Bar
        dbc.Row([
            # Return Reasons Donut
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Return Reasons Distribution", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="return-reason-donut", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=5, className="mb-4"),
            
            # Delay vs Return Rate Bar
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Impact of Shipping Delay on Return Rates", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="delay-return-bar", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=7, className="mb-4")
        ])
    ], fluid=True)

@callback(
    [
        Output("leak-kpi-total", "children"),
        Output("leak-kpi-rate", "children"),
        Output("leak-kpi-anomalies", "children"),
        Output("anomaly-table-container", "children"),
        Output("leakage-cat-bar", "figure"),
        Output("return-reason-donut", "figure"),
        Output("delay-return-bar", "figure")
    ],
    [
        Input("store-filters", "data"),
        Input("store-theme", "data")
    ]
)
def update_leakage_dashboard(filters, theme_data):
    dark_mode = theme_data.get("dark_mode", False) if theme_data else False
    theme = get_theme_colors(dark_mode)
    
    # 1. Fetch data
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    
    # 2. Run Isolation Forest
    detector = LeakageAnomalyDetector()
    if detector.load_model():
        scored_df = detector.predict(df)
    else:
        scored_df = detector.train(df)
        
    # 3. Apply Filters
    filtered_df = filter_dataframe(scored_df, filters)
    
    # 4. KPI Calculations
    total_leakage = filtered_df["leakage_amount"].sum()
    total_net = filtered_df["net_revenue"].sum()
    pricing_leakage = filtered_df["pricing_leakage"].sum()
    leakage_rate = total_leakage / (total_net + pricing_leakage) if (total_net + pricing_leakage) > 0 else 0.0
    
    num_anomalies = filtered_df["is_anomaly"].sum()

    leak_str = f"${total_leakage:,.0f}" if total_leakage >= 1000 else f"${total_leakage:,.2f}"
    card_total = create_kpi_card("Total Leakage", leak_str, theme["danger"], "Gross revenue lost to leakage", dark_mode)
    card_rate = create_kpi_card("Leakage Rate", f"{leakage_rate*100:.1f}%", theme["warning"], "Leakage share of billing basis", dark_mode)
    card_anomalies = create_kpi_card("ML Flagged Audits", f"{num_anomalies:,}", theme["primary"], "Suspicious transactions count", dark_mode)

    # 5. Isolation Forest Anomaly Table
    anomaly_orders = filtered_df[filtered_df["is_anomaly"] == 1].sort_values(by="leakage_amount", ascending=False)
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Order ID"),
            html.Th("Customer"),
            html.Th("Sales Rep"),
            html.Th("Status"),
            html.Th("Delay (Days)"),
            html.Th("Discount"),
            html.Th("Leakage Amount"),
            html.Th("Margin")
        ]))
    ]
    
    rows = []
    for _, r in anomaly_orders.head(30).iterrows():
        rows.append(html.Tr([
            html.Td(r["order_id"], style={"fontWeight": "bold"}),
            html.Td(r["customer_name"], style={"fontSize": "12px"}),
            html.Td(r["sales_rep_name"]),
            html.Td(r["order_status"]),
            html.Td(r["delay_days"]),
            html.Td(f"{r['discount_percentage']*100:.0f}%"),
            html.Td(f"${r['leakage_amount']:,.2f}", style={"color": theme["danger"], "fontWeight": "bold"}),
            html.Td(f"{r['profit_margin']*100:.1f}%")
        ]))
        
    table_body = [html.Tbody(rows)]
    bootstrap_table = dbc.Table(
        table_header + table_body,
        bordered=True,
        hover=True,
        striped=True,
        responsive=True,
        style={"color": theme["text"], "backgroundColor": theme["card_bg"], "borderColor": theme["grid"], "fontSize": "12px"}
    )
    
    # 6. Leakage Category & Cause Stacked Bar (NEW VISUAL)
    leakage_by_cat = filtered_df.groupby("category")[["discount_leakage", "return_leakage", "delay_leakage", "pricing_leakage"]].sum().reset_index()
    melted_leakage = leakage_by_cat.melt(id_vars="category", var_name="leakage_type", value_name="amount")
    melted_leakage["leakage_type"] = melted_leakage["leakage_type"].str.replace("_leakage", "").str.title() + " Leakage"
    
    colors_leak = [theme["primary"], theme["danger"], theme["warning"], theme["accent"]]
    fig_leak_cat = px.bar(
        melted_leakage, x="category", y="amount", color="leakage_type",
        color_discrete_sequence=colors_leak,
        labels={"amount": "Leakage Amount ($)", "category": "Category", "leakage_type": "Leakage Cause"},
        barmode="stack"
    )
    fig_leak_cat.update_layout(
        title=dict(text="Revenue Leakage Distribution by Category & Operational Cause", font=dict(size=14)),
        margin=dict(t=40, b=40, l=40, r=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    apply_plotly_theme(fig_leak_cat, dark_mode)

    # 7. Return Reasons Donut Chart
    returns_df = filtered_df[filtered_df["order_status"] == "Returned"]
    if not returns_df.empty:
        reasons = returns_df.groupby("return_reason")["order_id"].count().reset_index()
        colors_reasons = [theme["primary"], theme["accent"], theme["danger"], theme["warning"]]
        fig_donut = px.pie(
            reasons, values="order_id", names="return_reason",
            color_discrete_sequence=colors_reasons,
            hole=0.4
        )
    else:
        fig_donut = go.Figure()
        fig_donut.add_annotation(text="No returns found in search results", showarrow=False, font=dict(size=14, color=theme["text_muted"]))
        
    fig_donut.update_layout(
        title=dict(text="Return Reasons Analysis", font=dict(size=14)),
        margin=dict(t=40, b=40, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    apply_plotly_theme(fig_donut, dark_mode)

    # 8. Shipping Delay vs Return Rate (Bar chart)
    delay_stats = filtered_df.groupby("delay_days").agg({
        "is_returned": "mean",
        "order_id": "count"
    }).reset_index()
    
    delay_stats = delay_stats[delay_stats["order_id"] >= 3].sort_values(by="delay_days")
    
    fig_bar = px.bar(
        delay_stats, x="delay_days", y="is_returned",
        color_continuous_scale="Reds",
        color="is_returned",
        labels={"delay_days": "Shipping Delay (Days)", "is_returned": "Return Rate (%)"},
    )
    fig_bar.update_layout(
        title=dict(text="Average Return Rate by Delivery Delay Days", font=dict(size=14)),
        yaxis=dict(tickformat=".0%"),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_bar, dark_mode)
    fig_bar.update_coloraxes(showscale=False)
    
    return card_total, card_rate, card_anomalies, bootstrap_table, fig_leak_cat, fig_donut, fig_bar
