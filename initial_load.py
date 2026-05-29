import time
import request
import pandas as pd
from sqlalchemy import create_engine, text


DB_USER = ''  
DB_PASSWORD = ''
DB_HOST = '' 
DB_PORT = ''
DB_NAME = '' 

FRED_API_KEY = ''

engine_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(engine_url)

def initialize_database():
    """Creates the Star Schema tables in PostgreSQL if they do not exist."""
    print("Initializing database schema...")
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
    print("Schema initialization complete.")

def load_dimension_data():
    """Loads the static metadata for the tracked supply chain commodities."""
    print("Loading dimension data...")
    dim_data = {
        'series_id': ['WPU091503', 'PCU331110331110', 'PCU484121484121'],
        'title': ['PPI: Corrugated and Solid Fiber Boxes', 'PPI: Iron and Steel Mills', 'PPI: General Freight Trucking, Long-Distance'],
        'frequency': ['Monthly', 'Monthly', 'Monthly'],
        'units': ['Index', 'Index', 'Index']
    }
    df_dim = pd.DataFrame(dim_data)
    
    try:
        df_dim.to_sql('dim_series', engine, if_exists='append', index=False)
        print("Dimension table successfully populated.")
    except Exception as e:
        print("Note: Dimension data already exists (Primary Key constraint). Skipping insert.")

def extract_and_load_facts():
    """Pulls historical pricing data from the FRED API and loads it into the fact table."""
    print("Starting FRED API extraction...")
    series_list = ['WPU091503', 'PCU331110331110', 'PCU484121484121']
    all_observations = []

    for series in series_list:
        print(f"Fetching data for Series: {series}")
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series}&api_key={FRED_API_KEY}&file_type=json"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['observations'])
            df['series_id'] = series
            df = df[['series_id', 'date', 'value']] 
            df = df.rename(columns={'date': 'observation_date'})
            df['value'] = pd.to_numeric(df['value'], errors='coerce') 
            
            clean_df = df.dropna(subset=['value']) 
            
            all_observations.append(clean_df)
        else:
            print(f"Failed to extract {series}. API Status Code: {response.status_code}")
            
        time.sleep(1)

    if all_observations:
        print("Merging and loading fact data to PostgreSQL...")
        final_fact_df = pd.concat(all_observations, ignore_index=True)
        

        final_fact_df.to_sql('fact_observations', engine, if_exists='replace', index=False)
        print(f"Success! Loaded {len(final_fact_df)} observation records into fact_observations.")
    else:
        print("No data extracted. Check your API key and network connection.")


if __name__ == "__main__":
    print("=== Supply Chain Analytics: Initial Load Pipeline ===")
    initialize_database()
    load_dimension_data()
    extract_and_load_facts()
    print("=== Pipeline Execution Complete ===")
