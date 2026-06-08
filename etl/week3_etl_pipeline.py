import os
import time
import logging
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- 1. Path & Credential Configuration ---
# Finds .env in the project root (one level up from this /etl folder)
root_dir = Path(__file__).resolve().parent.parent
dotenv_path = root_dir / '.env'

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Fail-Fast Validation: Ensure required variables are set
REQUIRED_VARS = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'FRED_API_KEY']
missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}. "
                           f"Ensure your .env file exists at {dotenv_path} and contains these keys.")

# Configuration
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))
DB_NAME = os.getenv('DB_NAME')
FRED_API_KEY = os.getenv('FRED_API_KEY')

engine_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(engine_url)

SERIES_LIST = ['WPU091503', 'PCU331110331110', 'PCU484121484121']

# --- 2. Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)

# --- 3. Database Initialization ---
def initialize_database():
    logging.info("Verifying database schema...")
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
        observation_year INT,
        observation_month INT,
        value NUMERIC
    );
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        logging.info("Database schema verified.")
    except SQLAlchemyError as e:
        logging.error(f"Database initialization failed: {e}")

# --- 4. Incremental Load Logic ---
def get_latest_observation_date(series_id):
    query = text("SELECT MAX(observation_date) FROM fact_observations WHERE series_id = :sid")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"sid": series_id}).scalar()
            if result:
                if isinstance(result, str):
                    result = datetime.strptime(result, '%Y-%m-%d').date()
                next_date = result + timedelta(days=1)
                return next_date.strftime('%Y-%m-%d')
            return "2015-01-01"
    except SQLAlchemyError as e:
        logging.error(f"Failed to query max date for {series_id}: {e}")
        return "2015-01-01"

# --- 5. Extraction Layer ---
def extract_api_data(series_id, start_date):
    logging.info(f"Extracting {series_id} starting from {start_date}...")
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&observation_start={start_date}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data.get('observations', []))
    except requests.exceptions.RequestException as e:
        logging.error(f"API Request failed for {series_id}: {e}")
        return pd.DataFrame()

# --- 6. Transformation Layer ---
def transform_data(df, series_id):
    if df.empty: return df
    logging.info(f"Transforming {len(df)} rows for {series_id}...")
    df['series_id'] = series_id
    df = df[['series_id', 'date', 'value']].copy()
    df.rename(columns={'date': 'observation_date'}, inplace=True)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.dropna(subset=['value'], inplace=True)
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    df['observation_year'] = df['observation_date'].dt.year
    df['observation_month'] = df['observation_date'].dt.month
    return df

# --- 7. Validation Layer ---
def validate_data(df):
    if df.empty: return False
    logging.info("Executing Data Quality Checks...")
    if df.isnull().values.any() or (df['value'] < 0).any():
        logging.error("Data Quality Check Failed.")
        return False
    return True

# --- 8. Load Layer ---
def load_data(df):
    try:
        df.to_sql('fact_observations', engine, if_exists='append', index=False)
        logging.info(f"Successfully loaded {len(df)} records.")
    except Exception as e:
        logging.error(f"Failed to load: {e}")

# --- 9. Main Orchestration ---
def main():
    logging.info("=== Starting Supply Chain ETL Pipeline ===")
    initialize_database()
    for series in SERIES_LIST:
        start_date = get_latest_observation_date(series)
        raw_df = extract_api_data(series, start_date)
        clean_df = transform_data(raw_df, series)
        if validate_data(clean_df):
            load_data(clean_df)
        time.sleep(1)
    logging.info("=== ETL Pipeline Complete ===")

if __name__ == "__main__":
    main()