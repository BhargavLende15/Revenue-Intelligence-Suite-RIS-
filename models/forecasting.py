import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

def train_and_forecast_revenue(df, forecast_months=6):
    """
    Groups net revenue by month, fits a Linear Regression with lag and trend features,
    and returns a forecast for the next `forecast_months` months with confidence intervals.
    """
    # 1. Aggregate monthly sales
    monthly_sales = df.groupby("month")["net_revenue"].sum().reset_index()
    monthly_sales = monthly_sales.sort_values(by="month").reset_index(drop=True)
    
    n_history = len(monthly_sales)
    if n_history < 6:
        # Fallback if there is not enough historical data
        print("Warning: Not enough monthly data points to perform regression. Returning simple average.")
        mean_val = monthly_sales["net_revenue"].mean()
        forecast = pd.DataFrame({
            "month": [f"Future Month {i+1}" for i in range(forecast_months)],
            "forecasted_revenue": [mean_val] * forecast_months,
            "lower_ci": [mean_val * 0.9] * forecast_months,
            "upper_ci": [mean_val * 1.1] * forecast_months
        })
        return monthly_sales, forecast

    # 2. Engineer features for history
    monthly_sales["trend"] = range(1, n_history + 1)
    
    # Seasonality (Sine/Cosine of Month)
    months = pd.to_datetime(monthly_sales["month"] + "-01").dt.month
    monthly_sales["month_sin"] = np.sin(2 * np.pi * months / 12)
    monthly_sales["month_cos"] = np.cos(2 * np.pi * months / 12)
    
    # Lag Features (1, 2, and 3 months)
    monthly_sales["lag_1"] = monthly_sales["net_revenue"].shift(1)
    monthly_sales["lag_2"] = monthly_sales["net_revenue"].shift(2)
    monthly_sales["lag_3"] = monthly_sales["net_revenue"].shift(3)
    
    # Drop rows with NaN (first 3 rows due to lag_3)
    train_data = monthly_sales.dropna().copy()
    
    # Define features and target
    features = ["trend", "month_sin", "month_cos", "lag_1", "lag_2", "lag_3"]
    X = train_data[features]
    y = train_data["net_revenue"]
    
    # 3. Fit Linear Regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate residuals standard error for confidence intervals
    preds = model.predict(X)
    residuals = y - preds
    rse = np.sqrt(np.sum(residuals**2) / (len(y) - len(features)))
    
    # 4. Generate future forecasts iteratively
    last_row = monthly_sales.iloc[-1]
    last_month_dt = datetime.strptime(last_row["month"] + "-01", "%Y-%m-%d")
    
    future_months = []
    future_revenue = []
    
    # Let's keep a history buffer to pull lags from
    history_rev = list(monthly_sales["net_revenue"])
    current_trend = n_history
    
    for i in range(forecast_months):
        # Calculate future date
        next_month_dt = last_month_dt
        for _ in range(i + 1):
            if next_month_dt.month == 12:
                next_month_dt = datetime(next_month_dt.year + 1, 1, 1)
            else:
                next_month_dt = datetime(next_month_dt.year, next_month_dt.month + 1, 1)
                
        next_month_str = next_month_dt.strftime("%Y-%m")
        future_months.append(next_month_str)
        
        current_trend += 1
        m_num = next_month_dt.month
        m_sin = np.sin(2 * np.pi * m_num / 12)
        m_cos = np.cos(2 * np.pi * m_num / 12)
        
        # Pull lags from the history_rev buffer
        l1 = history_rev[-1]
        l2 = history_rev[-2]
        l3 = history_rev[-3]
        
        X_pred = pd.DataFrame([{
            "trend": current_trend,
            "month_sin": m_sin,
            "month_cos": m_cos,
            "lag_1": l1,
            "lag_2": l2,
            "lag_3": l3
        }], columns=features)
        
        pred_val = model.predict(X_pred)[0]
        future_revenue.append(pred_val)
        history_rev.append(pred_val) # Feed back prediction to act as future lag
        
    # Calculate prediction intervals (standard 95% confidence interval using 1.96 * RSE)
    # RSE increases slightly as we project further out due to error propagation
    forecast_df = pd.DataFrame({
        "month": future_months,
        "forecasted_revenue": future_revenue
    })
    forecast_df["lower_ci"] = [max(0.0, r - (1.96 * rse * np.sqrt(1 + 0.1 * step))) for step, r in enumerate(future_revenue)]
    forecast_df["upper_ci"] = [r + (1.96 * rse * np.sqrt(1 + 0.1 * step)) for step, r in enumerate(future_revenue)]
    
    return monthly_sales, forecast_df
