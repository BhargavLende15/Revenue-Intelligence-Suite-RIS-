import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from analytics.sql_executor import run_raw_query
from utils.helpers import get_theme_colors, filter_dataframe
from analytics.executive_insights import generate_executive_insights

dash.register_page(__name__, path="/report")

def layout():
    return dbc.Container([
        # Header Row (With Print Button)
        dbc.Row([
            dbc.Col([
                html.H2("Corporate Executive Report", className="mb-0", style={"fontWeight": "700"}),
                html.P("Compile dynamic business reports and print summary findings.", className="text-muted", style={"fontSize": "14px"})
            ], width=9),
            dbc.Col([
                dbc.Button([
                    html.I(className="fas fa-print me-2"), "Print Report"
                ], id="btn-print-report", color="primary", className="float-end shadow-sm", style={"borderRadius": "8px"})
            ], width=3, className="d-flex align-items-center justify-content-end")
        ], className="mb-4 d-print-none"),
        
        # Report Body Card
        dbc.Card([
            dbc.CardBody([
                # Report Header
                html.Div([
                    html.H3("REVENUE INTELLIGENCE AUDIT & STATUS REPORT", style={"fontWeight": "800", "textAlign": "center", "color": "#212529"}),
                    html.H5("Corporate Financial & Operational Review", style={"fontWeight": "600", "textAlign": "center", "color": "#6C757D", "borderBottom": "2px solid #212529", "paddingBottom": "15px"}),
                    html.Div([
                        html.P([html.Strong("Reporting Period: "), "July 2024 - June 2026"], style={"margin": "0"}),
                        html.P([html.Strong("System Model version: "), "RIS-v1.0 (Random Forest / K-Means / Isolation Forest)"], style={"margin": "0"}),
                    ], style={"display": "flex", "justifyContent": "space-between", "fontSize": "12px", "color": "#6C757D", "marginTop": "10px", "marginBottom": "30px"})
                ]),
                
                # Executive Summary Section
                html.Div([
                    html.H5("1. Executive Summary", style={"fontWeight": "700", "borderBottom": "1px solid #6C757D", "paddingBottom": "5px", "color": "#333"}),
                    html.P("This document reviews key performance indicators, regional performance metrics, marketing spend effectiveness, and operational revenue leakage across all product categories. Analysis is powered by SQLite data analytics coupled with scikit-learn anomaly detection and segmentation models.", style={"fontSize": "13px", "lineHeight": "1.6"}),
                ], className="mb-4"),
                
                # Financial Indicators Table
                html.Div([
                    html.H5("2. Core Financial Indicators", style={"fontWeight": "700", "borderBottom": "1px solid #6C757D", "paddingBottom": "5px", "color": "#333"}),
                    html.Div(id="report-financial-table-container", className="mb-4")
                ]),
                
                # Operational Performance Summary
                html.Div([
                    html.H5("3. Operational Review & Leakage Breakdown", style={"fontWeight": "700", "borderBottom": "1px solid #6C757D", "paddingBottom": "5px", "color": "#333"}),
                    html.P([
                        "Operational revenue leakage has been aggregated across four vectors: excessive discounts (discounts exceeding a standard 20% threshold), returns, shipping delays leading to order cancellations, and list-price invoices discrepancy (pricing leakage). "
                    ], style={"fontSize": "13px", "lineHeight": "1.6"}),
                    html.Div(id="report-operational-summary", className="mb-4")
                ]),
                
                # Actionable Recommendations
                html.Div([
                    html.H5("4. Quantitative Business Recommendations", style={"fontWeight": "700", "borderBottom": "1px solid #6C757D", "paddingBottom": "5px", "color": "#333"}),
                    html.P("The Revenue Intelligence Suite recommends the following strategic reallocations and controls based directly on data signals:", style={"fontSize": "13px"}),
                    html.Div(id="report-recs-table-container")
                ]),
                
                # Footer signature block
                html.Div([
                    html.Div([
                        html.P("Prepared by: Revenue Intelligence Suite (RIS) Engine", style={"margin": "0", "fontStyle": "italic"}),
                        html.P("System Audit Date: 2026-07-19", style={"margin": "0", "fontStyle": "italic"})
                    ], style={"borderTop": "1px solid #E9ECEF", "paddingTop": "15px", "marginTop": "40px", "textAlign": "right", "fontSize": "11px", "color": "#6C757D"})
                ])
            ], style={"padding": "40px"})
        ], id="printable-report-card", style={"borderRadius": "12px", "boxShadow": "0 4px 10px rgba(0,0,0,0.08)", "border": "1px solid #E9ECEF", "backgroundColor": "#FFFFFF"})
    ], fluid=True)

# Callback to handle Print
app = dash.get_app()
app.clientside_callback(
    """
    function(n_clicks) {
        if(n_clicks > 0) {
            window.print();
        }
        return null;
    }
    """,
    Output("btn-print-report", "n_clicks"),
    Input("btn-print-report", "n_clicks"),
    prevent_initial_call=True
)

@callback(
    [
        Output("report-financial-table-container", "children"),
        Output("report-operational-summary", "children"),
        Output("report-recs-table-container", "children")
    ],
    [
        Input("store-filters", "data")
    ]
)
def update_report(filters):
    # Report is printed in a white card, so we pull standard light colors
    
    # 1. Fetch data
    df = run_raw_query("SELECT * FROM master_analytical_dataset")
    spend_df = run_raw_query("SELECT * FROM marketing_spend")
    targets_df = run_raw_query("SELECT * FROM monthly_targets")
    
    # 2. Filter
    filtered_df = filter_dataframe(df, filters)
    
    # Apply targets filters
    filtered_targets = targets_df.copy()
    if filters and filters.get("region") != "All":
        if len(filtered_df) > 0:
            filtered_targets = filtered_targets[filtered_targets["region_id"] == filtered_df["region_id"].iloc[0]]
        else:
            filtered_targets = filtered_targets[filtered_targets["region_id"] == "N/A"]
    if filters and filters.get("year") != "All":
        filtered_targets = filtered_targets[filtered_targets["target_month"].str.startswith(str(filters["year"]))]
        
    total_target = filtered_targets["target_revenue"].sum()

    # 3. Calculations
    total_gross = filtered_df["gross_revenue"].sum()
    discounts = filtered_df["discount_amount"].sum()
    net_rev = filtered_df["net_revenue"].sum()
    profit = filtered_df["gross_profit"].sum()
    margin = profit / net_rev if net_rev > 0 else 0.0
    orders_count = filtered_df["order_id"].nunique()
    
    target_ach = (net_rev / total_target * 100) if total_target > 0 else 100.0
    
    discount_leak = filtered_df["discount_leakage"].sum()
    return_leak = filtered_df["return_leakage"].sum()
    delay_leak = filtered_df["delay_leakage"].sum()
    price_leak = filtered_df["pricing_leakage"].sum()
    total_leak = filtered_df["leakage_amount"].sum()
    leakage_rate = total_leak / (net_rev + price_leak) if (net_rev + price_leak) > 0 else 0.0

    # 4. Create Financial indicators table
    fin_table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Metric Header"),
            html.Th("Aggregate Value", style={"textAlign": "right"}),
            html.Th("Percentage Contribution / Margin", style={"textAlign": "right"}),
            html.Th("Reference Benchmark / Baseline")
        ])),
        html.Tbody([
            html.Tr([
                html.Td("Gross Invoiced Sales"),
                html.Td(f"${total_gross:,.2f}", style={"textAlign": "right"}),
                html.Td("100.0%", style={"textAlign": "right"}),
                html.Td("Raw sales baseline prior to discounts")
            ]),
            html.Tr([
                html.Td("Campaign Discounts Issued"),
                html.Td(f"-${discounts:,.2f}", style={"textAlign": "right", "color": "#DC3545"}),
                html.Td(f"{discounts/total_gross*100:.1f}% of Gross", style={"textAlign": "right", "color": "#DC3545"}),
                html.Td("Target average discount cap is 15%")
            ]),
            html.Tr([
                html.Td("Net Realized Revenue"),
                html.Td(f"${net_rev:,.2f}", style={"textAlign": "right", "fontWeight": "bold"}),
                html.Td(f"{net_rev/total_gross*100:.1f}% of Gross", style={"textAlign": "right"}),
                html.Td(f"Target Revenue: ${total_target:,.2f} ({target_ach:.1f}% achieved)")
            ]),
            html.Tr([
                html.Td("Gross Cost Basis"),
                html.Td(f"-${filtered_df['cost_amount'].sum():,.2f}", style={"textAlign": "right"}),
                html.Td(f"{filtered_df['cost_amount'].sum()/net_rev*100:.1f}% of Net", style={"textAlign": "right"}),
                html.Td("Includes platform, license, hardware cost bounds")
            ]),
            html.Tr([
                html.Td("Net Realized Profit"),
                html.Td(f"${profit:,.2f}", style={"textAlign": "right", "fontWeight": "bold", "color": "#28A745"}),
                html.Td(f"{margin*100:.1f}% Net Margin", style={"textAlign": "right", "fontWeight": "bold", "color": "#28A745"}),
                html.Td("Target margin is 45.0%")
            ])
        ])
    ], bordered=True, hover=True, striped=True, style={"fontSize": "13px"})

    # 5. Operational Summary Text
    insights_data = generate_executive_insights(filtered_df, spend_df, targets_df)
    
    op_summary_html = [
        html.Div([
            html.P([
                html.Strong("Leakage Vector Details: "),
                html.Span(f"Total leakage of "),
                html.Strong(f"${total_leak:,.2f} "),
                html.Span(f"represents an overall leakage rate of "),
                html.Strong(f"{leakage_rate*100:.1f}% "),
                html.Span("against billing baselines. Categorical review indicates the highest exposure lies within the "),
                html.Strong(f"'{insights_data['highest_leakage_category']}' "),
                html.Span(f"category, which suffered ") ,
                html.Strong(f"${insights_data['highest_leakage_category_amount']:,.2f} "),
                html.Span("in leakage losses.")
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div("DISCOUNT LEAKAGE", style={"fontSize": "10px", "color": "#6C757D", "fontWeight": "600"}),
                        html.H4(f"${discount_leak:,.2f}", style={"fontWeight": "700", "color": "#E63946", "margin": "0"})
                    ], className="p-2 border rounded text-center bg-light")
                ], width=6, sm=3, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Div("RETURNED LEAKAGE", style={"fontSize": "10px", "color": "#6C757D", "fontWeight": "600"}),
                        html.H4(f"${return_leak:,.2f}", style={"fontWeight": "700", "color": "#E63946", "margin": "0"})
                    ], className="p-2 border rounded text-center bg-light")
                ], width=6, sm=3, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Div("DELAY CANCEL LEAKAGE", style={"fontSize": "10px", "color": "#6C757D", "fontWeight": "600"}),
                        html.H4(f"${delay_leak:,.2f}", style={"fontWeight": "700", "color": "#E63946", "margin": "0"})
                    ], className="p-2 border rounded text-center bg-light")
                ], width=6, sm=3, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Div("PRICING LEAKAGE", style={"fontSize": "10px", "color": "#6C757D", "fontWeight": "600"}),
                        html.H4(f"${price_leak:,.2f}", style={"fontWeight": "700", "color": "#E63946", "margin": "0"})
                    ], className="p-2 border rounded text-center bg-light")
                ], width=6, sm=3, className="mb-2"),
            ], className="mb-3")
        ])
    ]

    # 6. Actionable recommendations table
    recs_rows = []
    for idx, rec in enumerate(insights_data["recommendations"]):
        recs_rows.append(html.Tr([
            html.Td(idx + 1, style={"fontWeight": "bold"}),
            html.Td(rec["action"], style={"fontWeight": "600"}),
            html.Td(rec["rationale"]),
            html.Td(rec["impact"], style={"color": "#DC3545" if rec["impact"] == "High" else "#FFC107" if rec["impact"] == "Medium" else "#17A2B8", "fontWeight": "700"})
        ]))
        
    recs_table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("#"),
            html.Th("Action Requirement"),
            html.Th("Quantitative Rationale"),
            html.Th("Business Priority")
        ])),
        html.Tbody(recs_rows)
    ], bordered=True, hover=True, striped=True, style={"fontSize": "13px"})

    return fin_table, op_summary_html, recs_table
