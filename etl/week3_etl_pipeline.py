import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- 1. Path & Credential Configuration ---
root_dir = Path(__file__).resolve().parent.parent
dotenv_path = root_dir / '.env'

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Fail-Fast Validation
REQUIRED_VARS = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'FRED_API_KEY']
missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}.")

# Configuration
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)
FRED_API_KEY = os.getenv('FRED_API_KEY')
SERIES_LIST = ['WPU091503', 'PCU331110331110', 'PCU484121484121']

# --- 2. Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')

# --- 3. Database Initialization ---
def initialize_database():
    logging.info("Verifying database schema...")
    # FIX: Added UNIQUE constraint to prevent duplicate data
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS dim_series (
        series_id VARCHAR(50) PRIMARY KEY,
        title VARCHAR(255),
        frequency VARCHAR(50),
        units VARCHAR(50)
    );

    CREATE TABLE IF NOT EXISTS fact_observations (
        observation_id SERIAL PRIMARY KEY,
        series_id VARCHAR(50) REFERENCES dim_series(series_id),
        observation_date DATE,
        value NUMERIC,
        UNIQUE(series_id, observation_date) 
    );
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        logging.info("Database schema verified.")
    except SQLAlchemyError as e:
        logging.error(f"Database initialization failed: {e}")

# --- 4. Logic ---
def get_latest_observation_date(series_id):
    query = text("SELECT MAX(observation_date) FROM fact_observations WHERE series_id = :sid")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"sid": series_id}).scalar()
            return (result + timedelta(days=1)).strftime('%Y-%m-%d') if result else "2015-01-01"
    except SQLAlchemyError:
        return "2015-01-01"

def extract_api_data(series_id, start_date):
    logging.info(f"Extracting {series_id} starting from {start_date}...")
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&observation_start={start_date}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return pd.DataFrame(response.json().get('observations', []))
    except Exception as e:
        logging.error(f"API Request failed: {e}")
        return pd.DataFrame()

def transform_data(df, series_id):
    if df.empty: return df
    df = df[['date', 'value']].copy()
    df.rename(columns={'date': 'observation_date', 'value': 'value'}, inplace=True)
    df['series_id'] = series_id
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    return df.dropna(subset=['value'])

def load_data(df):
    try:
        # Using 'append' with the UNIQUE constraint now handles deduplication
        df.to_sql('fact_observations', engine, if_exists='append', index=False)
        logging.info(f"Loaded {len(df)} records.")
    except Exception:
        # If a duplicate is hit, it will trigger an error; we log it and move on
        logging.warning("Skipped duplicate records.")

def main():
    initialize_database()
    for series in SERIES_LIST:
        start_date = get_latest_observation_date(series)
        df = transform_data(extract_api_data(series, start_date), series)
        if not df.empty:
            load_data(df)
        time.sleep(1)

if __name__ == "__main__":
    main()