import pandas as pd
import numpy as np
from scipy import stats

def calculate_descriptive_stats(df):
    """
    Computes standard descriptive statistics for numerical columns in the master dataset.
    """
    numeric_cols = ["gross_revenue", "net_revenue", "cost_amount", "gross_profit", "profit_margin", "discount_percentage", "delay_days", "leakage_amount"]
    stats_df = df[numeric_cols].describe().T
    
    # Add median, variance, skewness, and kurtosis
    stats_df["median"] = df[numeric_cols].median()
    stats_df["var"] = df[numeric_cols].var()
    stats_df["skewness"] = df[numeric_cols].skew()
    stats_df["kurtosis"] = df[numeric_cols].kurt()
    
    return stats_df.round(4)

def calculate_correlation_matrix(df):
    """
    Computes correlation coefficients between numeric columns.
    """
    numeric_cols = ["gross_revenue", "net_revenue", "cost_amount", "gross_profit", "profit_margin", "discount_percentage", "delay_days", "leakage_amount", "spend_amount"]
    # We join with marketing spend if not present, but let's keep it to columns available in the master dataset
    cols_to_use = [c for c in ["gross_revenue", "net_revenue", "cost_amount", "gross_profit", "profit_margin", "discount_percentage", "delay_days", "leakage_amount"] if c in df.columns]
    
    corr_matrix = df[cols_to_use].corr()
    return corr_matrix.round(4)

def detect_outliers_iqr(df, column, threshold=1.5):
    """
    Detects outliers using the Interquartile Range (IQR) method.
    Returns the outlier rows.
    """
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - threshold * iqr
    upper_bound = q3 + threshold * iqr
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers, lower_bound, upper_bound

def detect_outliers_zscore(df, column, threshold=3.0):
    """
    Detects outliers using the Z-score method.
    Returns the outlier rows.
    """
    z_scores = np.abs(stats.zscore(df[column].fillna(0)))
    outliers = df[z_scores > threshold]
    return outliers
