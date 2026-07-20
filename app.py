import os
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
from analytics.sql_executor import run_raw_query, get_db_connection
from etl.generate_data import generate_enterprise_data
from etl.pipeline import run_etl_pipeline
from utils.helpers import get_sidebar_layout, get_theme_colors

# 1. Automatic Database Bootstrapping
db_path = "database/revenue_intelligence.db"
if not os.path.exists(db_path):
    print("Database not found! Initializing data generation and ETL pipeline...")
    generate_enterprise_data()
    run_etl_pipeline()

# 2. Extract filter options dynamically from the DB
regions = ["All"] + sorted(run_raw_query("SELECT DISTINCT region_name FROM master_analytical_dataset")["region_name"].dropna().tolist())
segments = ["All"] + sorted(run_raw_query("SELECT DISTINCT customer_segment FROM master_analytical_dataset")["customer_segment"].dropna().tolist())
categories = ["All"] + sorted(run_raw_query("SELECT DISTINCT category FROM master_analytical_dataset")["category"].dropna().tolist())
channels = ["All"] + sorted(run_raw_query("SELECT DISTINCT sales_channel FROM master_analytical_dataset")["sales_channel"].dropna().tolist())
years = ["All"] + sorted([str(y) for y in run_raw_query("SELECT DISTINCT year FROM master_analytical_dataset")["year"].dropna().tolist()])

# 3. Create Dash application pointing to pages folder
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="dashboard/pages",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css" # FontAwesome Icons
    ],
    title="Revenue Intelligence Suite"
)

# Expose server for potential deployment (e.g. gunicorn)
server = app.server

# 4. Global Sidebar & Filters
def get_sidebar(dark_mode=False):
    theme = get_theme_colors(dark_mode)
    
    # Navigation Links structured
    nav_links = []
    for page in dash.page_registry.values():
        icon = "fas fa-tachometer-alt"
        if page["name"] == "Revenue":
            icon = "fas fa-chart-line"
        elif page["name"] == "Customers":
            icon = "fas fa-users"
        elif page["name"] == "Products":
            icon = "fas fa-box"
        elif page["name"] == "Leakage":
            icon = "fas fa-exclamation-triangle"
        elif page["name"] == "Forecasting":
            icon = "fas fa-magic"
        elif page["name"] == "Report":
            icon = "fas fa-file-invoice"
            
        nav_links.append(
            dbc.NavLink([
                html.I(className=f"{icon} me-2"), page["name"]
            ], href=page["relative_path"], active="exact", className="mb-2", style={"borderRadius": "8px"})
        )
        
    sidebar_style = get_sidebar_layout(dark_mode)
    
    return html.Div([
        # Branding
        html.Div([
            html.I(className="fas fa-layer-group me-2 text-primary", style={"fontSize": "22px"}),
            html.H4("RIS Dashboard", className="d-inline mb-0", style={"fontWeight": "800", "letterSpacing": "0.5px"})
        ], className="mb-4 d-flex align-items-center", style={"borderBottom": f"1px solid {theme['grid']}", "paddingBottom": "15px"}),
        
        # Navigation
        html.Div([
            html.H6("ANALYTICS PAGES", style={"color": theme["text_muted"], "fontSize": "11px", "fontWeight": "600", "letterSpacing": "1px", "textTransform": "uppercase"} , className="mb-2"),
            dbc.Nav(nav_links, vertical=True, pills=True, className="mb-4")
        ]),
        
        # Interactive Filters
        html.Div([
            html.H6("INTERACTIVE FILTERS", style={"color": theme["text_muted"], "fontSize": "11px", "fontWeight": "600", "letterSpacing": "1px", "textTransform": "uppercase"}, className="mb-2"),
            
            html.Div([
                dbc.Label("Year", style={"fontSize": "12px", "fontWeight": "500", "margin": "0"}),
                dcc.Dropdown(id="filter-year", options=[{"label": y, "value": y} for y in years], value="All", clearable=False, className="mb-2", style={"fontSize": "12px"}),
                
                dbc.Label("Region", style={"fontSize": "12px", "fontWeight": "500", "margin": "0"}),
                dcc.Dropdown(id="filter-region", options=[{"label": r, "value": r} for r in regions], value="All", clearable=False, className="mb-2", style={"fontSize": "12px"}),
                
                dbc.Label("Customer Segment", style={"fontSize": "12px", "fontWeight": "500", "margin": "0"}),
                dcc.Dropdown(id="filter-segment", options=[{"label": s, "value": s} for s in segments], value="All", clearable=False, className="mb-2", style={"fontSize": "12px"}),
                
                dbc.Label("Product Category", style={"fontSize": "12px", "fontWeight": "500", "margin": "0"}),
                dcc.Dropdown(id="filter-category", options=[{"label": c, "value": c} for c in categories], value="All", clearable=False, className="mb-2", style={"fontSize": "12px"}),
                
                dbc.Label("Sales Channel", style={"fontSize": "12px", "fontWeight": "500", "margin": "0"}),
                dcc.Dropdown(id="filter-channel", options=[{"label": ch, "value": ch} for ch in channels], value="All", clearable=False, className="mb-3", style={"fontSize": "12px"})
            ])
        ]),
        
        # Theme toggle (Light / Dark switch)
        html.Div([
            dbc.Checklist(
                options=[{"label": "Enable Dark Mode", "value": 1}],
                value=[],
                id="theme-switch",
                switch=True,
                style={"fontSize": "12px", "fontWeight": "500", "color": theme["text"]}
            )
        ], style={"position": "absolute", "bottom": "20px", "left": "20px", "right": "20px"})
    ], style=sidebar_style, id="sidebar")

# 5. Core Layout Structure
app.layout = html.Div([
    # Stores for global variables
    dcc.Store(id="store-filters", data={}),
    dcc.Store(id="store-theme", data={"dark_mode": False}),
    
    # Sidebar
    html.Div(get_sidebar(dark_mode=False), id="sidebar-container"),
    
    # Main Dashboard Page Content area
    html.Div([
        dash.page_container
    ], id="main-content", style={
        "marginLeft": "260px",
        "padding": "2rem",
        "transition": "all 0.3s",
        "minHeight": "100vh"
    })
], id="layout-root")

# 6. Global Callbacks
@app.callback(
    [
        Output("sidebar-container", "children"),
        Output("store-theme", "data"),
        Output("main-content", "style"),
        Output("layout-root", "style")
    ],
    [
        Input("theme-switch", "value")
    ],
    [
        State("store-theme", "data")
    ]
)
def toggle_theme(switch_val, theme_store):
    dark_mode = True if switch_val and 1 in switch_val else False
    theme = get_theme_colors(dark_mode)
    
    # Generate sidebar layout
    sidebar = get_sidebar(dark_mode)
    
    # Update content box style
    content_style = {
        "marginLeft": "260px",
        "padding": "2rem",
        "transition": "all 0.3s",
        "minHeight": "100vh",
        "backgroundColor": theme["bg"],
        "color": theme["text"]
    }
    
    root_style = {
        "backgroundColor": theme["bg"],
        "minHeight": "100vh"
    }
    
    return sidebar, {"dark_mode": dark_mode}, content_style, root_style

@app.callback(
    Output("store-filters", "data"),
    [
        Input("filter-year", "value"),
        Input("filter-region", "value"),
        Input("filter-segment", "value"),
        Input("filter-category", "value"),
        Input("filter-channel", "value")
    ]
)
def update_filters(year, region, segment, category, channel):
    return {
        "year": year,
        "region": region,
        "segment": segment,
        "category": category,
        "channel": channel
    }

if __name__ == "__main__":
    app.run(debug=True, port=8050)
