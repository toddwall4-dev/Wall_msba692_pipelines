# Supply Chain Commodity Analytics Pipeline

## Executive Summary
This project provides an end-to-end data engineering solution designed to monitor supply chain commodity volatility. By integrating live data from the Federal Reserve Economic Data (FRED) API into a PostgreSQL-backed data warehouse, this system enables procurement teams to track inflationary trends in critical sectors—specifically Corrugated Boxes, Iron/Steel, and Long-Distance Freight.

## System Architecture

Our pipeline follows a standard extract-transform-load (ETL) pattern designed for scalability and data integrity:

* **Extraction:** An incremental load script queries the database for the latest available record, ensuring we only fetch new data from the FRED API.
* **Transformation & Validation:** Data is standardized, null values are removed, and derived fields (year/month) are generated. A rigorous quality framework ensures no corrupt data enters the system.
* **Storage:** A Star Schema database design in PostgreSQL stores dimensions and observations, utilizing unique constraints to prevent data duplication.
* **Analytics:** A Plotly Dash dashboard connects directly to the warehouse, providing real-time visualization and KPI tracking for procurement decision-making.

## Key Features
* **Automated Incremental Loading:** Reduces API bandwidth and ensures the database is always up-to-date.
* **Data Integrity:** Unique constraints and automated validation logic ensure a reliable "source of truth."
* **Interactive Analytics:** A web-based dashboard allows stakeholders to toggle between commodities and view historical trends.

## Project Structure
project-root/
├── dash_app/           # Plotly Dash application
├── docs/               # Project proposals and diagrams
├── etl/                # Production ETL scripts
├── images/             # Visual assets
├── notebooks/          # Exploratory Data Analysis (EDA)
├── sql/                # SQL Schema definitions
├── .env.example        # Environment variable template
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation

## Setup Instructions

### 1. Prerequisites
Ensure you have PostgreSQL installed and running. Create a target database named `supplychain_db`.

### 2. Environment Setup
1. Clone this repository.
2. Create a `.env` file in the root directory (based on `.env.example`) and fill in your details:

DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=supplychain_db
FRED_API_KEY=your_key_here

understand. Here is the raw Markdown code for that section. You can copy the content inside the box below, then paste it directly into your README.md file.
Markdown
## Setup Instructions

### 1. Prerequisites
Ensure you have PostgreSQL installed and running. Create a target database named `supplychain_db`.

### 2. Environment Setup
1. Clone this repository.
2. Create a `.env` file in the root directory (based on `.env.example`) and fill in your details:

```text
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=supplychain_db
FRED_API_KEY=your_key_here

### 3. Execution

* **Install Dependencies:** `pip install -r requirements.txt`
* **Initialize Database:** `python3 etl/initial_load.py`
* **Run Pipeline:** `python3 etl/week3_etl_pipeline.py`
* **Launch Dashboard:** `python3 dash_app/app.py`  
  *(Navigate to http://127.0.0.1:8050/ in your browser)*