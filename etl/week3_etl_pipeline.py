import time
import requests
import logging
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- 1. Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)

# --- 2. Configuration & Credentials ---
DB_USER = 'postgres'  
DB_PASSWORD = 'YOUR_PASSWORD_HERE'
DB_HOST = 'YOUR_SERVER_IP_HERE' 
DB_PORT = '5432'
DB_NAME = 'supplychain_db' 

FRED_API_KEY = 'YOUR_API_KEY_HERE'

engine_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(engine_url)

SERIES_LIST = ['WPU091503', 'PCU331110331110', 'PCU484121484121']

# --- 3. Database Initialization ---
def initialize_database():
    """Ensures tables exist and updates the schema for derived metrics."""
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
    """Queries the database to find the most recent data point for a series."""
    query = text("SELECT MAX(observation_date) FROM fact_observations WHERE series_id = :sid")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"sid": series_id}).scalar()
            if result:
                # Convert string to datetime if necessary, then add 1 day
                if isinstance(result, str):
                    result = datetime.strptime(result, '%Y-%m-%d').date()
                next_date = result + timedelta(days=1)
                return next_date.strftime('%Y-%m-%d')
            return "2015-01-01" # Default start date if table is empty
    except SQLAlchemyError as e:
        logging.error(f"Failed to query max date for {series_id}: {e}")
        return "2015-01-01"

# --- 5. Extraction Layer ---
def extract_api_data(series_id, start_date):
    """Extracts raw JSON data from the FRED API."""
    logging.info(f"Extracting {series_id} starting from {start_date}...")
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&observation_start={start_date}"
    
    try:
        # Extended timeout to 30 seconds to prevent API drops
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data.get('observations', []))
    except requests.exceptions.RequestException as e:
        logging.error(f"API Request failed for {series_id}: {e}")
        return pd.DataFrame() # Return empty DF on failure

# --- 6. Transformation Layer ---
def transform_data(df, series_id):
    """Cleans data and calculates derived metrics."""
    if df.empty:
        return df
        
    logging.info(f"Transforming {len(df)} rows for {series_id}...")
    
    df['series_id'] = series_id
    df = df[['series_id', 'date', 'value']].copy()
    df.rename(columns={'date': 'observation_date'}, inplace=True)
    
    # Clean values
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df.dropna(subset=['value'], inplace=True)
    
    # Add Derived Metrics (Year and Month for Aggregation Layers)
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    df['observation_year'] = df['observation_date'].dt.year
    df['observation_month'] = df['observation_date'].dt.month
    
    return df

# --- 7. Validation & Data Quality Layer ---
def validate_data(df):
    """Executes data quality checks before loading."""
    if df.empty:
        logging.warning("Validation skipped: DataFrame is empty. No new records to process.")
        return False
        
    logging.info("Executing Data Quality Checks...")
    
    # Check 1: Null Values
    if df.isnull().values.any():
        logging.error("Data Quality Check Failed: Null values detected in transformed data.")
        return False
        
    # Check 2: Range Validation (Prices cannot be negative)
    if (df['value'] < 0).any():
        logging.error("Data Quality Check Failed: Negative values detected in pricing index.")
        return False
        
    # Check 3: Schema Validation
    expected_columns = ['series_id', 'observation_date', 'value', 'observation_year', 'observation_month']
    if not all(col in df.columns for col in expected_columns):
        logging.error("Data Quality Check Failed: Missing expected columns.")
        return False
        
    logging.info(f"Data Quality Checks Passed. {len(df)} rows validated.")
    return True

# --- 8. Load Layer ---
def load_data(df):
    """Appends validated data to the PostgreSQL database."""
    try:
        df.to_sql('fact_observations', engine, if_exists='append', index=False)
        logging.info(f"Successfully loaded {len(df)} records into PostgreSQL.")
    except Exception as e:
        logging.error(f"Failed to load data into database: {e}")

# --- 9. Main Orchestration ---
def main():
    logging.info("=== Starting Supply Chain ETL Pipeline ===")
    initialize_database()
    
    total_records_loaded = 0
    
    for series in SERIES_LIST:
        start_date = get_latest_observation_date(series)
        raw_df = extract_api_data(series, start_date)
        
        clean_df = transform_data(raw_df, series)
        
        if validate_data(clean_df):
            load_data(clean_df)
            total_records_loaded += len(clean_df)
            
        time.sleep(1) # Rate limit protection
        
    logging.info(f"=== ETL Pipeline Complete. Total new records appended: {total_records_loaded} ===")

if __name__ == "__main__":
    main()