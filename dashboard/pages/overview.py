import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from analytics.sql_executor import run_raw_query
from utils.helpers import create_kpi_card, get_theme_colors, apply_plotly_theme, filter_dataframe
from analytics.root_cause import analyze_revenue_drop
from analytics.executive_insights import generate_executive_insights

dash.register_page(__name__, path="/")

def layout():
    return dbc.Container([
        # Page Title Row
        dbc.Row([
            dbc.Col([
                html.H2("Revenue Intelligence Suite", className="mb-0", style={"fontWeight": "700"}),
                html.P("Real-time enterprise KPIs, trends, and automated business insights.", className="text-muted", style={"fontSize": "14px"})
            ], width=12)
        ], className="mb-4"),
        
        # KPI Cards Row (No Logos/Icons)
        dbc.Row([
            dbc.Col(id="kpi-revenue", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-profit", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-margin", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-orders", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-customers", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-leakage", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-target", width=12, sm=6, md=4, lg=3, className="mb-3"),
            dbc.Col(id="kpi-forecast", width=12, sm=6, md=4, lg=3, className="mb-3"),
        ], className="mb-4"),
        
        # Row 1: Revenue Trends & Category Share
        dbc.Row([
            # Revenue & Profit Trend Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Revenue & Profit Trends", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="trend-chart", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=8, className="mb-4"),
            
            # Category Share Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Revenue by Category", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="category-pie", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=4, className="mb-4")
        ]),
        
        # Row 2: MoM Growth & Regional Quotas (NEW VISUALS)
        dbc.Row([
            # MoM Growth rate Bar
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Month-over-Month Revenue Growth Rate", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="growth-rate-bar", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=6, className="mb-4"),
            
            # Regional Quota compare Bar
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Territory Sales Performance vs Target", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="quota-attainment-bar", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=6, className="mb-4")
        ]),
        
        # Insights & Alerts Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.I(className="fas fa-brain me-2", style={"color": "#7209B7"}),
                            html.H5("AI-Powered Root-Cause Analysis & Executive Alerts", className="d-inline mb-0", style={"fontSize": "16px", "fontWeight": "600"})
                        ])
                    ),
                    dbc.CardBody(id="executive-insights-container")
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12)
        ], className="mb-4")
    ], fluid=True)

@callback(
    [
        Output("kpi-revenue", "children"),
        Output("kpi-profit", "children"),
        Output("kpi-margin", "children"),
        Output("kpi-orders", "children"),
        Output("kpi-customers", "children"),
        Output("kpi-leakage", "children"),
        Output("kpi-target", "children"),
        Output("kpi-forecast", "children"),
        Output("trend-chart", "figure"),
        Output("category-pie", "figure"),
        Output("growth-rate-bar", "figure"),
        Output("quota-attainment-bar", "figure"),
        Output("executive-insights-container", "children")
    ],
    [
        Input("store-filters", "data"),
        Input("store-theme", "data")
    ]
)
def update_overview(filters, theme_data):
    dark_mode = theme_data.get("dark_mode", False) if theme_data else False
    theme = get_theme_colors(dark_mode)
    
    # 1. Fetch fresh data from DB
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    spend_df = run_raw_query("SELECT * FROM marketing_spend")
    targets_df = run_raw_query("SELECT * FROM monthly_targets")
    
    # Check if there is forecasting table (forecast is generated in model run)
    try:
        forecast_df = run_raw_query("SELECT * FROM forecast_data")
        total_forecast_rev = forecast_df["forecasted_revenue"].sum()
    except Exception:
        total_forecast_rev = df["net_revenue"].mean() * 6 # fallback estimate

    # 2. Filter data
    filtered_df = filter_dataframe(df, filters)
    
    # For targets, filter by region and year if set
    filtered_targets = targets_df.copy()
    if filters and filters.get("region") != "All":
        if len(filtered_df) > 0:
            filtered_targets = filtered_targets[filtered_targets["region_id"] == filtered_df["region_id"].iloc[0]]
        else:
            filtered_targets = filtered_targets[filtered_targets["region_id"] == "N/A"]
    if filters and filters.get("year") != "All":
        filtered_targets = filtered_targets[filtered_targets["target_month"].str.startswith(str(filters["year"]))]
        
    total_target = filtered_targets["target_revenue"].sum()

    # 3. Calculate KPI Metrics
    total_rev = filtered_df["net_revenue"].sum()
    total_profit = filtered_df["gross_profit"].sum()
    profit_margin = total_profit / total_rev if total_rev > 0 else 0.0
    total_orders = filtered_df["order_id"].nunique()
    total_cust = filtered_df["customer_id"].nunique()
    total_leakage = filtered_df["leakage_amount"].sum()
    
    target_achievement = (total_rev / total_target * 100) if total_target > 0 else 100.0

    # 4. Format KPIs (No icons)
    rev_str = f"${total_rev:,.0f}" if total_rev >= 1000 else f"${total_rev:,.2f}"
    profit_str = f"${total_profit:,.0f}" if total_profit >= 1000 else f"${total_profit:,.2f}"
    leak_str = f"${total_leakage:,.0f}" if total_leakage >= 1000 else f"${total_leakage:,.2f}"
    forecast_str = f"${total_forecast_rev:,.0f}"
    
    card_rev = create_kpi_card("Total Revenue", rev_str, theme["primary"], "Net sales post discounts", dark_mode)
    card_profit = create_kpi_card("Total Profit", profit_str, theme["success"], "Net profit margin contribution", dark_mode)
    card_margin = create_kpi_card("Profit Margin", f"{profit_margin*100:.1f}%", theme["info"], "Gross margin score", dark_mode)
    card_orders = create_kpi_card("Orders", f"{total_orders:,}", theme["accent"], "Volume of processed orders", dark_mode)
    card_cust = create_kpi_card("Customers", f"{total_cust:,}", theme["warning"], "Active buying client list", dark_mode)
    card_leakage = create_kpi_card("Revenue Leakage", leak_str, theme["danger"], "Estimated leakage amount", dark_mode)
    card_target = create_kpi_card("Target Achievement", f"{target_achievement:.1f}%", theme["secondary"], f"Target: ${total_target:,.0f}", dark_mode)
    card_forecast = create_kpi_card("6M Forecast", forecast_str, theme["primary"], "Projected revenue next 6M", dark_mode)

    # 5. Trend Chart (Monthly Net Revenue & Profit)
    monthly_trend = filtered_df.groupby("month").agg({"net_revenue": "sum", "gross_profit": "sum"}).reset_index()
    monthly_trend = monthly_trend.sort_values(by="month")
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_trend["month"], y=monthly_trend["net_revenue"],
        name="Net Revenue", line=dict(color=theme["primary"], width=3),
        mode="lines+markers"
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly_trend["month"], y=monthly_trend["gross_profit"],
        name="Gross Profit", line=dict(color=theme["success"], width=3),
        mode="lines+markers"
    ))
    fig_trend.update_layout(
        title=dict(text="Monthly Financial Performance", font=dict(size=14)),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    apply_plotly_theme(fig_trend, dark_mode)

    # 6. Category Pie Chart
    cat_rev = filtered_df.groupby("category")["net_revenue"].sum().reset_index()
    colors_pie = [theme["primary"], theme["success"], theme["accent"], theme["warning"]]
    fig_pie = px.pie(
        cat_rev, values="net_revenue", names="category",
        color_discrete_sequence=colors_pie,
        hole=0.4
    )
    fig_pie.update_layout(
        title=dict(text="Revenue Share by Category", font=dict(size=14)),
        margin=dict(t=40, b=40, l=10, r=10),
        legend=dict(orientation="v")
    )
    apply_plotly_theme(fig_pie, dark_mode)

    # 7. Growth Rate Bar Chart (NEW VISUAL)
    monthly_trend["prev_revenue"] = monthly_trend["net_revenue"].shift(1)
    monthly_trend["growth_rate"] = (monthly_trend["net_revenue"] - monthly_trend["prev_revenue"]) / monthly_trend["prev_revenue"]
    monthly_trend["growth_rate"] = monthly_trend["growth_rate"].fillna(0.0)
    
    growth_colors = [theme["success"] if g >= 0 else theme["danger"] for g in monthly_trend["growth_rate"]]
    
    fig_growth = go.Figure(go.Bar(
        x=monthly_trend["month"], y=monthly_trend["growth_rate"],
        marker_color=growth_colors,
        text=[f"{g*100:+.1f}%" if g != 0 else "" for g in monthly_trend["growth_rate"]],
        textposition="outside"
    ))
    fig_growth.update_layout(
        title=dict(text="Month-over-Month Revenue Growth Rate (%)", font=dict(size=14)),
        yaxis=dict(tickformat=".0%"),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_growth, dark_mode)

    # 8. Region Revenue vs Sales Quota (NEW VISUAL)
    reg_sales_summary = filtered_df.groupby("region_name")["net_revenue"].sum().reset_index()
    reg_tg = targets_df.groupby("region_id")["target_revenue"].sum().reset_index()
    
    # Map region_id in reg_tg to region_name
    reg_name_map = dict(zip(df["region_id"], df["region_name"]))
    reg_tg["region_name"] = reg_tg["region_id"].map(reg_name_map)
    
    reg_compare = reg_sales_summary.merge(reg_tg, on="region_name", how="outer").fillna(0.0)
    
    fig_reg_compare = go.Figure()
    fig_reg_compare.add_trace(go.Bar(
        x=reg_compare["region_name"], y=reg_compare["net_revenue"],
        name="Realized Net Revenue", marker_color=theme["primary"]
    ))
    fig_reg_compare.add_trace(go.Bar(
        x=reg_compare["region_name"], y=reg_compare["target_revenue"],
        name="Quota Target", marker_color=theme["secondary"]
    ))
    fig_reg_compare.update_layout(
        title=dict(text="Revenue realization vs Quota Target by Territory", font=dict(size=14)),
        barmode="group",
        margin=dict(t=40, b=40, l=40, r=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    apply_plotly_theme(fig_reg_compare, dark_mode)

    # 9. Root-Cause Analysis & Executive Alerts
    drop_analysis = analyze_revenue_drop(filtered_df)
    insights_data = generate_executive_insights(filtered_df, spend_df, targets_df)
    
    insights_html = []
    
    # Analysis of MoM drops
    if drop_analysis["status"] == "decline":
        insights_html.append(dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            html.Strong("Revenue Decline Alert: "),
            html.Span(drop_analysis["message"])
        ], color="danger", style={"borderRadius": "8px", "padding": "12px", "fontSize": "14px"}, className="mb-3"))
    else:
        insights_html.append(dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Revenue Growth: "),
            html.Span(drop_analysis["message"])
        ], color="success", style={"borderRadius": "8px", "padding": "12px", "fontSize": "14px"}, className="mb-3"))
        
    highlights = [
        html.Div([
            html.Strong("Top Performing Product: "),
            html.Span(f"{insights_data['top_performing_product']} (${insights_data['top_performing_product_revenue']:,.2f})")
        ], className="mb-2", style={"fontSize": "14px"}),
        html.Div([
            html.Strong("Highest Value Customer: "),
            html.Span(f"{insights_data['highest_value_customer']} (${insights_data['highest_value_customer_revenue']:,.2f})")
        ], className="mb-2", style={"fontSize": "14px"}),
        html.Div([
            html.Strong("Worst Performing Region: "),
            html.Span(f"{insights_data['worst_performing_region']} ({insights_data['worst_performing_region_achievement']*100:.1f}% Target Achieved)")
        ], className="mb-2", style={"fontSize": "14px"}),
        html.Div([
            html.Strong("Highest Leakage Category: "),
            html.Span(f"{insights_data['highest_leakage_category']} (${insights_data['highest_leakage_category_amount']:,.2f})")
        ], className="mb-2", style={"fontSize": "14px"})
    ]
    
    recs_list = []
    for rec in insights_data["recommendations"]:
        badge_color = "danger" if rec["impact"] == "High" else "warning" if rec["impact"] == "Medium" else "info"
        recs_list.append(html.Li([
            dbc.Badge(rec["impact"], color=badge_color, className="me-2", style={"fontSize": "10px"}),
            html.Strong(rec["action"] + " "),
            html.Span(rec["rationale"], style={"color": theme["text_muted"], "fontSize": "13px"})
        ], className="mb-2"))
        
    insights_html.append(dbc.Row([
        dbc.Col([
            html.H6("Executive Highlights", style={"fontWeight": "600", "borderBottom": f"1px solid {theme['grid']}", "paddingBottom": "8px"}),
            html.Div(highlights)
        ], width=12, md=5, className="mb-3"),
        dbc.Col([
            html.H6("Recommended Actions", style={"fontWeight": "600", "borderBottom": f"1px solid {theme['grid']}", "paddingBottom": "8px"}),
            html.Ul(recs_list, style={"paddingLeft": "15px", "listStyleType": "square", "fontSize": "14px"})
        ], width=12, md=7)
    ]))
    
    return [
        card_rev, card_profit, card_margin, card_orders,
        card_cust, card_leakage, card_target, card_forecast,
        fig_trend, fig_pie, fig_growth, fig_reg_compare, insights_html
    ]
