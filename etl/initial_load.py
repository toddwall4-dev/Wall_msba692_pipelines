import os
import time
import logging
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- 1. Path & Credential Configuration ---
# Finds .env in the project root
root_dir = Path(__file__).resolve().parent.parent
dotenv_path = root_dir / '.env'

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Fail-Fast Validation: Ensure we don't proceed without credentials
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

# --- 2. Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
)

# --- 3. Database Initialization ---
def initialize_database():
    logging.info("Initializing database schema...")
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
        value NUMERIC
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_tables_sql))
        conn.commit()
    logging.info("Schema initialization complete.")

# --- 4. Dimension Load ---
def load_dimension_data():
    logging.info("Loading dimension data...")
    dim_data = {
        'series_id': ['WPU091503', 'PCU331110331110', 'PCU484121484121'],
        'title': ['PPI: Corrugated and Solid Fiber Boxes', 'PPI: Iron and Steel Mills', 'PPI: General Freight Trucking, Long-Distance'],
        'frequency': ['Monthly', 'Monthly', 'Monthly'],
        'units': ['Index', 'Index', 'Index']
    }
    df_dim = pd.DataFrame(dim_data)
    
    try:
        df_dim.to_sql('dim_series', engine, if_exists='append', index=False)
        logging.info("Dimension table successfully populated.")
    except Exception:
        logging.warning("Dimension data likely already exists. Skipping insert.")

# --- 5. Fact Load ---
def extract_and_load_facts():
    logging.info("Starting FRED API initial extraction...")
    series_list = ['WPU091503', 'PCU331110331110', 'PCU484121484121']
    all_observations = []

    for series in series_list:
        logging.info(f"Fetching data for Series: {series}")
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series}&api_key={FRED_API_KEY}&file_type=json"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data.get('observations', []))
            if not df.empty:
                df['series_id'] = series
                df = df[['series_id', 'date', 'value']] 
                df = df.rename(columns={'date': 'observation_date'})
                df['value'] = pd.to_numeric(df['value'], errors='coerce') 
                all_observations.append(df.dropna(subset=['value']))
        except Exception as e:
            logging.error(f"Failed to extract {series}: {e}")
            
        time.sleep(1)

    if all_observations:
        logging.info("Merging and loading fact data to PostgreSQL...")
        final_fact_df = pd.concat(all_observations, ignore_index=True)
        final_fact_df.to_sql('fact_observations', engine, if_exists='replace', index=False)
        logging.info(f"Success! Loaded {len(final_fact_df)} observation records.")
    else:
        logging.error("No data extracted. Check your API key and network connection.")

if __name__ == "__main__":
    logging.info("=== Supply Chain Analytics: Initial Load Pipeline ===")
    initialize_database()
    load_dimension_data()
    extract_and_load_facts()
    logging.info("=== Pipeline Execution Complete ===")