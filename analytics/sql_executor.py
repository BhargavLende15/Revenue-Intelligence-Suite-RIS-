import os
import sqlite3
import pandas as pd

def get_db_connection():
    db_path = "database/revenue_intelligence.db"
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}. Please run the ETL pipeline first.")
    return sqlite3.connect(db_path)

def execute_sql_query(query_name, params=None):
    """
    Reads a SQL file from the sql/ folder, runs it on the SQLite database, and returns a DataFrame.
    """
    sql_file_path = f"sql/{query_name}.sql"
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL file not found at {sql_file_path}")
        
    with open(sql_file_path, "r") as f:
        query = f.read()
        
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df

def run_raw_query(query, params=None):
    """
    Executes a raw SQL query string on the database and returns a DataFrame.
    """
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df
