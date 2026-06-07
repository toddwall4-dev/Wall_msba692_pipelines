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
    pip install -r requirements.txt
4. Open `etl/week3_etl_pipeline.py` and update the Configuration block (Lines 16-20) with your local database credentials (specifically changing `DB_HOST` back to `localhost` or your local IP).
5. Insert your FRED API key into the `FRED_API_KEY` variable.
6. Execute the pipeline:
    python3 etl/week3_etl_pipeline.py

---

## Week 4: Analytics Dashboard (MVP)
This repository includes a Minimum Viable Product (MVP) dashboard built with Plotly Dash. It connects directly to the PostgreSQL database to visualize the engineered supply chain data.

**Business Insights:**
* **Macro-Economic Monitoring:** Allows procurement teams to track historical price volatility across critical supply chain sectors (Corrugated Boxes, Steel Mills, and General Freight).
* **Cost Forecasting:** The annual average aggregation helps identify long-term inflationary trends, enabling more accurate annual budgeting and contract negotiations.

**Features:**
* **Interactive Filtering:** Users can dynamically toggle between the three commodity indices without restarting the app.
* **KPI Card:** Displays the most recently available index value for immediate status checks.
* **Visualizations:** Renders a time-series trend line and an annual average bar chart.

**How to Run the Dash App:**
1. Open your terminal and ensure your PostgreSQL database is running.
2. Ensure you are in the root project directory.
3. Install dependencies: 
    pip install -r requirements.txt
4. Execute the application script: 
    python3 dashboard/app.py
5. Open a web browser and navigate to `http://127.0.0.1:8050/`.