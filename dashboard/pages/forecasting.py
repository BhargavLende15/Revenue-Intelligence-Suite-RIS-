import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from analytics.sql_executor import run_raw_query
from utils.helpers import get_theme_colors, apply_plotly_theme, filter_dataframe
from models.forecasting import train_and_forecast_revenue
from analytics.explainability import SHAPExplainerManager

dash.register_page(__name__, path="/forecasting")

def layout():
    # Load orders to populate transaction explainer select list
    df_orders = run_raw_query("SELECT order_id FROM orders LIMIT 100")
    order_options = [{"label": r["order_id"], "value": r["order_id"]} for _, r in df_orders.iterrows()]
    
    return dbc.Container([
        # Page Title Row
        dbc.Row([
            dbc.Col([
                html.H2("Predictive Forecasting & Explainable AI (SHAP)", className="mb-0", style={"fontWeight": "700"}),
                html.P("Project revenue trends and inspect machine learning decisions using SHAP values.", className="text-muted", style={"fontSize": "14px"})
            ], width=12)
        ], className="mb-4"),
        
        # Row 1: Forecast Graph
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("6-Month Net Revenue Time-Series Forecast", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="revenue-forecast-plot", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, className="mb-4")
        ]),
        
        # Row 2: SHAP Global and local waterfall
        dbc.Row([
            # SHAP Global
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Global Feature Importance (SHAP values)", className="mb-0", style={"fontSize": "16px", "fontWeight": "600"})),
                    dbc.CardBody([
                        dcc.Graph(id="shap-global-importance", config={"displayModeBar": False}),
                        html.P("Global feature importances calculate the average absolute impact a parameter has on the Random Forest regressor output.", style={"fontSize": "12px", "color": "#6C757D", "marginTop": "8px"})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=5, className="mb-4"),
            
            # SHAP Local Waterfall
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.Div([
                            html.H5("Explain a Transaction (Local SHAP Waterfall)", className="d-inline mb-0", style={"fontSize": "16px", "fontWeight": "600"}),
                            dcc.Dropdown(
                                id="shap-order-dropdown",
                                options=order_options,
                                value=order_options[0]["value"] if order_options else None,
                                clearable=False,
                                style={"width": "150px", "float": "right", "fontSize": "13px"}
                            )
                        ])
                    ),
                    dbc.CardBody([
                        dcc.Graph(id="shap-local-waterfall", config={"displayModeBar": False})
                    ])
                ], style={"borderRadius": "12px", "boxShadow": "0 4px 6px rgba(0,0,0,0.05)"})
            ], width=12, lg=7, className="mb-4")
        ])
    ], fluid=True)

@callback(
    [
        Output("revenue-forecast-plot", "figure"),
        Output("shap-global-importance", "figure"),
        Output("shap-local-waterfall", "figure")
    ],
    [
        Input("shap-order-dropdown", "value"),
        Input("store-filters", "data"),
        Input("store-theme", "data")
    ]
)
def update_forecasting_page(selected_order_id, filters, theme_data):
    dark_mode = theme_data.get("dark_mode", False) if theme_data else False
    theme = get_theme_colors(dark_mode)
    
    # 1. Fetch data
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    filtered_df = filter_dataframe(df, filters)
    
    # 2. Time-series Forecast
    # Run the forecaster (or query the cached forecast table if we save it)
    history, forecast = train_and_forecast_revenue(filtered_df)
    
    fig_forecast = go.Figure()
    
    # Historical Net Revenue
    fig_forecast.add_trace(go.Scatter(
        x=history["month"], y=history["net_revenue"],
        name="Historical Revenue", line=dict(color=theme["primary"], width=3),
        mode="lines+markers"
    ))
    
    # Forecasted Revenue
    fig_forecast.add_trace(go.Scatter(
        x=forecast["month"], y=forecast["forecasted_revenue"],
        name="Forecasted Revenue", line=dict(color=theme["success"], width=3, dash="dash"),
        mode="lines+markers"
    ))
    
    # Parse theme['success'] to RGBA for Plotly compatibility (no 8-char hex support)
    success_hex = theme['success'].lstrip('#')
    r = int(success_hex[0:2], 16)
    g = int(success_hex[2:4], 16)
    b = int(success_hex[4:6], 16)
    fillcolor_rgba = f"rgba({r}, {g}, {b}, 0.1)"

    # Confidence Interval Bands
    fig_forecast.add_trace(go.Scatter(
        x=list(forecast["month"]) + list(forecast["month"])[::-1],
        y=list(forecast["upper_ci"]) + list(forecast["lower_ci"])[::-1],
        fill="toself",
        fillcolor=fillcolor_rgba, # 10% opacity
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        name="95% Confidence Interval"
    ))
    
    fig_forecast.update_layout(
        title=dict(text="Revenue Projections & Forecast Confidence Band", font=dict(size=14)),
        margin=dict(t=40, b=40, l=40, r=40),
        hovermode="x unified"
    )
    apply_plotly_theme(fig_forecast, dark_mode)

    # Save forecast back to SQLite so overview page can read it quickly
    conn = run_raw_query("SELECT 1") # dummy query to trigger execution
    import sqlite3
    db_conn = sqlite3.connect("database/revenue_intelligence.db")
    forecast.to_sql("forecast_data", db_conn, if_exists="replace", index=False)
    db_conn.close()

    # 3. SHAP Global Feature Importance
    shap_manager = SHAPExplainerManager()
    # Check if explainer is trained, otherwise initialize
    if not shap_manager.load_explainer():
        shap_manager.initialize(df)
        
    global_importance_df = shap_manager.get_global_importance(df)
    
    fig_global = px.bar(
        global_importance_df, x="SHAP Importance", y="Feature",
        orientation="h",
        color_discrete_sequence=[theme["accent"]],
        labels={"SHAP Importance": "Average Absolute SHAP Impact", "Feature": "Feature Name"}
    )
    fig_global.update_layout(
        title=dict(text="Global Driver Strengths", font=dict(size=14)),
        margin=dict(t=40, b=40, l=40, r=40)
    )
    apply_plotly_theme(fig_global, dark_mode)

    # 4. SHAP Local Waterfall Explanation
    # Find details for selected order_id
    if selected_order_id:
        order_details = df[df["order_id"] == selected_order_id]
    else:
        order_details = df.head(1)
        
    if not order_details.empty:
        r = order_details.iloc[0]
        local_explanation = shap_manager.explain_local_prediction(
            category_str=r["category"],
            unit_price=float(r["unit_price"]),
            discount_pct=float(r["discount_percentage"]),
            region_str=r["region_name"],
            channel_str=r["sales_channel"],
            month_num=int(r["month_num"])
        )
        
        base_val = local_explanation["base_value"]
        pred_val = local_explanation["prediction"]
        conts = local_explanation["contributions"]
        
        # Prepare waterfall data vectors
        x_lbls = ["Base Value"]
        y_vals = [base_val]
        measures = ["absolute"]
        text_labels = [f"{base_val:.2f}"]
        
        for c in conts:
            x_lbls.append(f"{c['feature']}<br>({c['actual_value']})")
            y_vals.append(c["shap_value"])
            measures.append("relative")
            sign = "+" if c["shap_value"] >= 0 else ""
            text_labels.append(f"{sign}{c['shap_value']:.2f}")
            
        x_lbls.append("Prediction")
        y_vals.append(pred_val)
        measures.append("total")
        text_labels.append(f"{pred_val:.2f}")
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="SHAP Explanation",
            orientation="v",
            measure=measures,
            x=x_lbls,
            y=y_vals,
            text=text_labels,
            textposition="outside",
            connector={"line": {"color": theme["grid"], "width": 1.5}},
            decreasing={"marker": {"color": theme["danger"]}},
            increasing={"marker": {"color": theme["primary"]}},
            totals={"marker": {"color": theme["success"]}}
        ))
        
        fig_waterfall.update_layout(
            title=dict(text=f"SHAP Waterfall: Order {selected_order_id} Demand Explanation", font=dict(size=14)),
            margin=dict(t=40, b=40, l=40, r=40)
        )
        apply_plotly_theme(fig_waterfall, dark_mode)
    else:
        fig_waterfall = go.Figure()
        fig_waterfall.add_annotation(text="Selected order ID not found", showarrow=False)
        apply_plotly_theme(fig_waterfall, dark_mode)
        
    return fig_forecast, fig_global, fig_waterfall
