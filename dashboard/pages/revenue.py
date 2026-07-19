import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from analytics.sql_executor import run_raw_query
from utils.helpers import get_theme_colors, apply_plotly_theme, filter_dataframe

dash.register_page(__name__, path="/revenue")

def layout():
    return dbc.Container([
        # Page Title Row
        dbc.Row([
            dbc.Col([
                html.H2("Revenue & Profit Margin Analytics", className="mb-0", style={"fontWeight": "700"}),
                html.P("Granular breakdown of margins, categories, and channels.", className="text-muted", style={"fontSize": "14px"})
            ], width=12)
        ], className="mb-4"),
        
        # Row for Waterfall & Channels
        dbc.Row([
            # Waterfall Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Financial Waterfall (Sales Bridge)", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="waterfall-chart", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=8, className="mb-4"),
            
            # Sales Channels
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Sales Channel Mix", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="channel-donut", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=4, className="mb-4")
        ]),
        
        # Row for Category and Treemap
        dbc.Row([
            # Stacked Bar Monthly Category
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Monthly Category Revenue Breakdown", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="monthly-cat-bar", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=6, className="mb-4"),
            
            # Treemap
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Revenue Distribution by Geography & Category", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="revenue-treemap", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=6, className="mb-4")
        ])
    ], fluid=True)

@callback(
    [
        Output("waterfall-chart", "figure"),
        Output("channel-donut", "figure"),
        Output("monthly-cat-bar", "figure"),
        Output("revenue-treemap", "figure")
    ],
    [
        Input("store-filters", "data"),
        Input("store-theme", "data")
    ]
)
def update_revenue_analytics(filters, theme_data):
    dark_mode = theme_data.get("dark_mode", False) if theme_data else False
    theme = get_theme_colors(dark_mode)
    
    # 1. Fetch data
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    
    # 2. Filter
    filtered_df = filter_dataframe(df, filters)
    
    # 3. Create Waterfall Chart
    gross_rev = filtered_df["gross_revenue"].sum()
    discounts = filtered_df["discount_amount"].sum()
    net_rev = filtered_df["net_revenue"].sum()
    costs = filtered_df["cost_amount"].sum()
    profit = filtered_df["gross_profit"].sum()
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="Sales Bridge",
        orientation="v",
        measure=["relative", "relative", "total", "relative", "total"],
        x=["Gross Revenue", "Discounts", "Net Revenue", "Cost of Goods", "Net Profit"],
        textposition="outside",
        text=[f"${gross_rev:,.0f}", f"-${discounts:,.0f}", f"${net_rev:,.0f}", f"-${costs:,.0f}", f"${profit:,.0f}"],
        y=[gross_rev, -discounts, net_rev, -costs, profit],
        connector={"line": {"color": theme["grid"], "width": 1.5}},
        decreasing={"marker": {"color": theme["danger"]}},
        increasing={"marker": {"color": theme["primary"]}},
        totals={"marker": {"color": theme["success"]}}
    ))
    fig_waterfall.update_layout(
        title=dict(text="Revenue to Profit Sales Bridge", font=dict(size=14)),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_waterfall, dark_mode)
    
    # 4. Sales Channel Donut Chart
    chan_rev = filtered_df.groupby("sales_channel")["net_revenue"].sum().reset_index()
    colors_donut = [theme["primary"], theme["accent"], theme["warning"]]
    fig_donut = px.pie(
        chan_rev, values="net_revenue", names="sales_channel",
        color_discrete_sequence=colors_donut,
        hole=0.5
    )
    fig_donut.update_layout(
        title=dict(text="Revenue Share by Sales Channel", font=dict(size=14)),
        margin=dict(t=40, b=40, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    apply_plotly_theme(fig_donut, dark_mode)
    
    # 5. Monthly Category Revenue Stacked Bar
    monthly_cat = filtered_df.groupby(["month", "category"])["net_revenue"].sum().reset_index()
    monthly_cat = monthly_cat.sort_values(by="month")
    
    colors_bar = [theme["primary"], theme["success"], theme["accent"], theme["warning"]]
    fig_bar = px.bar(
        monthly_cat, x="month", y="net_revenue", color="category",
        color_discrete_sequence=colors_bar,
        labels={"net_revenue": "Net Revenue ($)", "month": "Month", "category": "Category"},
        barmode="stack"
    )
    fig_bar.update_layout(
        title=dict(text="Monthly Revenue Split by Category", font=dict(size=14)),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    apply_plotly_theme(fig_bar, dark_mode)
    
    # 6. Treemap (Region -> Category -> Product)
    fig_tree = px.treemap(
        filtered_df, path=["region_name", "category", "product_name"],
        values="net_revenue",
        color="net_revenue",
        color_continuous_scale="Viridis",
        labels={"net_revenue": "Revenue ($)", "labels": "Item"}
    )
    fig_tree.update_layout(
        title=dict(text="Revenue Treemap: Geography & Products", font=dict(size=14)),
        margin=dict(t=40, b=10, l=10, r=10)
    )
    apply_plotly_theme(fig_tree, dark_mode)
    fig_tree.update_coloraxes(showscale=False) # remove color bar to fit UI nicely
    
    return fig_waterfall, fig_donut, fig_bar, fig_tree
