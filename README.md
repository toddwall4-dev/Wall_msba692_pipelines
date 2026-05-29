# Supply Chain ETL Pipeline - MSBA 692

## Project Overview
This project contains a Python-based ETL pipeline that incrementally extracts supply chain commodity data (Corrugated Boxes, Steel, and Freight) from the Federal Reserve Economic Data (FRED) API. The data is transformed, validated through rigorous quality checks, and loaded into a local PostgreSQL database using a Star Schema. 

## Pipeline Architecture
1. **Extraction:** Queries PostgreSQL for the latest timestamp, dynamically adjusts the API payload, and fetches only new data (Incremental Load).
2. **Transformation:** Standardizes data types, drops missing values, and creates derived metrics (`observation_year` and `observation_month`).
3. **Data Quality Framework:** Enforces schema integrity, blocks null values, and validates positive numerical ranges before loading.
4. **Loading:** Connects to PostgreSQL via SQLAlchemy and appends validated rows.

## Setup Instructions
1. Install PostgreSQL locally.
2. Create a database named `supplychain_db`.
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt