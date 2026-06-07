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
2. Navigate to the `dashboard` directory.
3. Install dependencies: `pip install -r requirements.txt`
4. Execute the application script: `python3 app.py`
5. Open a web browser and navigate to `http://127.0.0.1:8050/`.