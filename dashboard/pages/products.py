import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
from analytics.sql_executor import run_raw_query, execute_sql_query
from utils.helpers import get_theme_colors, apply_plotly_theme, filter_dataframe
from models.demand_prediction import DemandPredictor, CATEGORY_MAP, REGION_MAP, CHANNEL_MAP

dash.register_page(__name__, path="/products")

def layout():
    return dbc.Container([
        # Page Title Row
        dbc.Row([
            dbc.Col([
                html.H2("Product Intelligence & ML Demand Simulator", className="mb-0", style={"fontWeight": "700"}),
                html.P("Analyze product viability, margins, underperforming catalog items, and simulate future demand.", className="text-muted", style={"fontSize": "14px"})
            ], width=12)
        ], className="mb-4"),
        
        # Row 1: Margins Scatter Plot & Worst Products
        dbc.Row([
            # Price vs Margin Scatter
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Product Profit Margin vs Selling Price", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="product-margin-scatter", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=7, className="mb-4"),
            
            # Underperforming Products Table
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Underperforming Products (SQL Profit & Returns)", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        html.Div(id="underperforming-products-container", style={"height": "350px", "overflowY": "auto"})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=5, className="mb-4")
        ]),
        
        # Row 2: ML Simulator Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.I(className="fas fa-sliders-h me-2", style={"color": "#3A86C8"}),
                            html.H5("Interactive ML Demand Prediction Simulator", className="d-inline mb-0", style={"fontSize": "16px", "fontWeight": "600"})
                        ])
                    ),
                    dbc.CardBody([
                        dbc.Row([
                            # Form Inputs
                            dbc.Col([
                                html.Form([
                                    dbc.Label("Product Category", className="mb-1", style={"fontSize": "13px", "fontWeight": "500"}),
                                    dcc.Dropdown(
                                        id="sim-category",
                                        options=[{"label": k, "value": k} for k in CATEGORY_MAP.keys()],
                                        value="Software",
                                        clearable=False,
                                        className="mb-3"
                                    ),
                                    
                                    dbc.Label("Unit Selling Price ($)", className="mb-1", style={"fontSize": "13px", "fontWeight": "500"}),
                                    dbc.Input(id="sim-price", type="number", value=1500, min=10, max=10000, step=10, className="mb-3"),
                                    
                                    dbc.Label("Discount Percentage (%)", className="mb-1", style={"fontSize": "13px", "fontWeight": "500"}),
                                    dbc.Input(id="sim-discount", type="number", value=10, min=0, max=80, step=1, className="mb-3"),
                                    
                                    dbc.Label("Target Region", className="mb-1", style={"fontSize": "13px", "fontWeight": "500"}),
                                    dcc.Dropdown(
                                        id="sim-region",
                                        options=[{"label": k, "value": k} for k in REGION_MAP.keys()],
                                        value="North America",
                                        clearable=False,
                                        className="mb-3"
                                    ),
                                    
                                    dbc.Label("Sales Channel", className="mb-1", style={"fontSize": "13px", "fontWeight": "500"}),
                                    dcc.Dropdown(
                                        id="sim-channel",
                                        options=[{"label": k, "value": k} for k in CHANNEL_MAP.keys()],
                                        value="Direct",
                                        clearable=False,
                                        className="mb-3"
                                    ),
                                    
                                    dbc.Label("Month of Sale (Seasonality)", className="mb-1", style={"fontSize": "13px", "fontWeight": "500"}),
                                    dcc.Slider(
                                        id="sim-month",
                                        min=1, max=12, step=1,
                                        marks={i: f"{i}" for i in range(1, 13)},
                                        value=10
                                    )
                                ])
                            ], width=12, md=6, lg=5),
                            
                            # Divider for layout
                            dbc.Col([
                                html.Div(style={"borderLeft": "1px solid #E9ECEF", "height": "100%", "margin": "0 auto"})
                            ], width=1, className="d-none d-md-block"),
                            
                            # Prediction Output Display
                            dbc.Col([
                                html.Div([
                                    html.H5("Prediction Output", className="mb-3", style={"fontWeight": "600"}),
                                    
                                    html.Div([
                                        html.Div("PREDICTED QUANTITY DEMAND", style={"fontSize": "12px", "color": "#6C757D", "fontWeight": "600"}),
                                        html.H1(id="sim-out-qty", style={"fontWeight": "800", "color": "#28A745", "margin": "0"}),
                                        html.Div("Estimated units sold per order", style={"fontSize": "11px", "color": "#A0A0A0"})
                                    ], className="p-3 mb-3 border rounded text-center", style={"backgroundColor": "#F8F9FA"}),
                                    
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div("EST. GROSS SALES", style={"fontSize": "11px", "color": "#6C757D", "fontWeight": "600"}),
                                            html.H4(id="sim-out-gross", style={"fontWeight": "700", "margin": "0"})
                                        ], width=6),
                                        dbc.Col([
                                            html.Div("EST. NET PROFIT", style={"fontSize": "11px", "color": "#6C757D", "fontWeight": "600"}),
                                            html.H4(id="sim-out-profit", style={"fontWeight": "700", "margin": "0"})
                                        ], width=6)
                                    ], className="text-center p-2 mb-3 border rounded"),
                                    
                                    dbc.Alert([
                                        html.I(className="fas fa-info-circle me-2"),
                                        html.Span("Calculation logic uses an ensemble Random Forest Regressor trained on historical order transaction items, accounting for unit cost baselines per category.")
                                    ], color="info", style={"fontSize": "12px", "borderRadius": "8px"})
                                ], style={"display": "flex", "flexDirection": "column", "justifyContent": "center", "height": "100%"})
                            ], width=12, md=5)
                        ])
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, className="mb-4")
        ])
    ], fluid=True)

@callback(
    [
        Output("product-margin-scatter", "figure"),
        Output("underperforming-products-container", "children")
    ],
    [
        Input("store-filters", "data"),
        Input("store-theme", "data")
    ]
)
def update_product_charts(filters, theme_data):
    dark_mode = theme_data.get("dark_mode", False) if theme_data else False
    theme = get_theme_colors(dark_mode)
    
    # 1. Fetch fresh master analytical dataset for scatter
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    filtered_df = filter_dataframe(df, filters)
    
    # 2. Scatter plot: price vs profit margin per item
    prod_metrics = filtered_df.groupby(["product_name", "category"]).agg({
        "unit_price": "mean",
        "profit_margin": "mean",
        "quantity": "sum"
    }).reset_index()
    
    colors_scatter = [theme["primary"], theme["success"], theme["accent"], theme["warning"]]
    fig_scatter = px.scatter(
        prod_metrics, x="unit_price", y="profit_margin", color="category",
        size="quantity", hover_data=["product_name"],
        color_discrete_sequence=colors_scatter,
        labels={"unit_price": "Average Invoice Unit Price ($)", "profit_margin": "Average Profit Margin", "category": "Category"}
    )
    fig_scatter.update_layout(
        title=dict(text="Average Selling Price vs Gross Margin", font=dict(size=14)),
        yaxis=dict(tickformat=".1%"),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_scatter, dark_mode)

    # 3. Underperforming Products (using worst_products.sql)
    # We query the worst products ranked. Since filter parameters in worst_products.sql are hard to filter post-hoc,
    # we'll display the global worst products list, which represents a product manager's portfolio level audit.
    worst_df = execute_sql_query("worst_products")
    
    # Setup Table
    table_header = [
        html.Thead(html.Tr([
            html.Th("Product Name"),
            html.Th("Category"),
            html.Th("Profit ($)"),
            html.Th("Margin (%)"),
            html.Th("Return Rate (%)")
        ]))
    ]
    
    rows = []
    for _, r in worst_df.head(10).iterrows():
        # Highlight negative profits in red
        profit_color = theme["danger"] if r["profit"] < 0 else theme["text"]
        margin_str = f"{r['profit_margin_pct']:.1f}%" if pd.notnull(r['profit_margin_pct']) else "0.0%"
        
        rows.append(html.Tr([
            html.Td(r["product_name"], style={"fontSize": "12px"}),
            html.Td(r["category"]),
            html.Td(f"${r['profit']:,.2f}", style={"color": profit_color, "fontWeight": "bold"}),
            html.Td(margin_str),
            html.Td(f"{r['return_rate_pct']:.1f}%")
        ]))
        
    table_body = [html.Tbody(rows)]
    bootstrap_table = dbc.Table(
        table_header + table_body,
        bordered=True,
        hover=True,
        striped=True,
        style={"color": theme["text"], "backgroundColor": theme["card_bg"], "borderColor": theme["grid"]}
    )
    
    return fig_scatter, bootstrap_table

@callback(
    [
        Output("sim-out-qty", "children"),
        Output("sim-out-gross", "children"),
        Output("sim-out-profit", "children")
    ],
    [
        Input("sim-category", "value"),
        Input("sim-price", "value"),
        Input("sim-discount", "value"),
        Input("sim-region", "value"),
        Input("sim-channel", "value"),
        Input("sim-month", "value")
    ]
)
def run_demand_simulator(category, price, discount_pct, region, channel, month):
    # Predictor
    predictor = DemandPredictor()
    if not predictor.load_model():
        # Fallback if model not trained
        df = run_raw_query("SELECT * FROM master_analytical_dataset")
        predictor.train(df)
        
    discount = discount_pct / 100.0
    
    # Run prediction
    pred_qty = predictor.predict_demand(
        category_str=category,
        unit_price=price,
        discount_pct=discount,
        region_str=region,
        channel_str=channel,
        month_num=month
    )
    
    # Get standard cost price factor for estimations
    # Categories: Software (0.2), Hardware (0.6), Consulting (0.6), Support (0.5)
    cost_factors = {"Software": 0.2, "Hardware": 0.63, "Consulting": 0.58, "Support": 0.45}
    cost_factor = cost_factors.get(category, 0.5)
    
    gross_sales = pred_qty * price * (1 - discount)
    cost_basis = pred_qty * price * cost_factor
    net_profit = gross_sales - cost_basis
    
    return (
        f"{pred_qty:.1f} Units",
        f"${gross_sales:,.2f}",
        f"${net_profit:,.2f}"
    )
