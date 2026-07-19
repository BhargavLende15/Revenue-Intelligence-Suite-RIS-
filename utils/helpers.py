import dash_bootstrap_components as dbc
from dash import html
import plotly.graph_objects as go
import plotly.io as pio

# Theme Colors
LIGHT_THEME = {
    "bg": "#F8F9FA",
    "card_bg": "#FFFFFF",
    "text": "#212529",
    "text_muted": "#6C757D",
    "primary": "#3A86C8",
    "secondary": "#6C757D",
    "success": "#28A745",
    "warning": "#FFC107",
    "danger": "#DC3545",
    "info": "#17A2B8",
    "leakage": "#E05A47",
    "grid": "#E9ECEF",
    "accent": "#4E73DF"
}

DARK_THEME = {
    "bg": "#121212",
    "card_bg": "#1E1E1E",
    "text": "#E0E0E0",
    "text_muted": "#A0A0A0",
    "primary": "#4EA8DE",
    "secondary": "#8E9AAF",
    "success": "#52B788",
    "warning": "#FAD2E1",
    "danger": "#E63946",
    "info": "#48CAE4",
    "leakage": "#F15BB5",
    "grid": "#2D2D2D",
    "accent": "#7209B7"
}

def get_theme_colors(dark_mode=False):
    return DARK_THEME if dark_mode else LIGHT_THEME

def apply_plotly_theme(fig, dark_mode=False):
    """
    Applies consistent theme styles to a Plotly figure.
    """
    theme = get_theme_colors(dark_mode)
    
    fig.update_layout(
        paper_bgcolor=theme["card_bg"],
        plot_bgcolor=theme["card_bg"],
        font=dict(color=theme["text"], family="Inter, sans-serif"),
        xaxis=dict(
            gridcolor=theme["grid"],
            linecolor=theme["grid"],
            zerolinecolor=theme["grid"]
        ),
        yaxis=dict(
            gridcolor=theme["grid"],
            linecolor=theme["grid"],
            zerolinecolor=theme["grid"]
        ),
        margin=dict(t=40, b=40, l=40, r=40),
        legend=dict(
            font=dict(color=theme["text"]),
            bgcolor="rgba(0,0,0,0)"
        )
    )
    return fig

def create_kpi_card(title, value, color, subtitle=None, dark_mode=False):
    """
    Generates a beautifully styled, rounded KPI card focusing on clean typography and value highlights.
    """
    theme = get_theme_colors(dark_mode)
    
    card_content = [
        html.Div([
            html.H6(title, style={"color": theme["text_muted"], "fontSize": "11px", "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.5px", "marginBottom": "4px"}),
            html.H3(value, style={"color": theme["text"], "fontWeight": "700", "margin": "0", "fontSize": "26px"}),
        ]),
    ]
    
    if subtitle:
        card_content.append(
            html.Div(subtitle, style={"fontSize": "11px", "color": theme["text_muted"], "marginTop": "6px", "fontWeight": "500"})
        )
        
    return html.Div(
        card_content,
        style={
            "backgroundColor": theme["card_bg"],
            "padding": "16px 20px",
            "borderRadius": "12px",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.03)" if not dark_mode else "0 4px 6px rgba(0,0,0,0.2)",
            "border": f"1px solid {theme['grid']}",
            "borderTop": f"4px solid {color}",
            "transition": "all 0.3s ease",
            "cursor": "default",
            "height": "100%"
        },
        className="kpi-card"
    )

def get_sidebar_layout(dark_mode=False):
    """
    Returns a unified sidebar layout.
    """
    theme = get_theme_colors(dark_mode)
    
    sidebar_style = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "260px",
        "padding": "2rem 1rem",
        "backgroundColor": theme["card_bg"],
        "borderRight": f"1px solid {theme['grid']}",
        "color": theme["text"],
        "zIndex": 1000,
        "transition": "all 0.3s"
    }
    
    # We can represent links as standard lists, which is then structured in app.py
    return sidebar_style

def filter_dataframe(df, filters):
    """
    Filters a pandas DataFrame based on global sidebar filter values.
    """
    if not filters:
        return df
        
    filtered = df.copy()
    
    if "year" in filters and filters["year"] != "All":
        filtered = filtered[filtered["year"] == int(filters["year"])]
        
    if "region" in filters and filters["region"] != "All":
        filtered = filtered[filtered["region_name"] == filters["region"]]
        
    if "segment" in filters and filters["segment"] != "All":
        filtered = filtered[filtered["customer_segment"] == filters["segment"]]
        
    if "category" in filters and filters["category"] != "All":
        filtered = filtered[filtered["category"] == filters["category"]]
        
    if "channel" in filters and filters["channel"] != "All":
        filtered = filtered[filtered["sales_channel"] == filters["channel"]]
        
    return filtered

