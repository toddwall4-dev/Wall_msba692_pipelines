# Supply Chain ETL Pipeline & Analytics Dashboard - MSBA 692

## Project Overview
This project contains a complete, end-to-end data engineering pipeline and web application. It extracts supply chain commodity data (Corrugated Boxes, Steel, and Freight) from the Federal Reserve Economic Data (FRED) API, processes it through a rigorous data quality framework, loads it into a PostgreSQL database, and serves the data through an interactive frontend web dashboard.

---

## Week 3: ETL Pipeline & Data Quality Engineering

### Pipeline Architecture
1. **Extraction:** Queries PostgreSQL for the latest timestamp, dynamically adjusts the API payload, and fetches only new data (Incremental Load).
2. **Transformation:** Standardizes data types, drops missing values, and creates derived metrics (`observation_year` and `observation_month`).
3. **Data Quality Framework:** Enforces schema integrity, blocks null values, and validates positive numerical ranges before loading.
4. **Loading:** Connects to PostgreSQL via SQLAlchemy and appends validated rows using a Star Schema structure.

### Setup Instructions & Execution
**Note for Grading:** This pipeline was developed and tested using a PostgreSQL container running on a remote Docker server. To reproduce this on your local machine, please follow these steps:

1. Ensure PostgreSQL is running locally or on a reachable server.
2. Create a target database named `supplychain_db`.
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
