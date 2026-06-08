import os
import dash
import pandas as pd
import plotly.express as px
from pathlib import Path
from dotenv import load_dotenv
from dash import dcc, html, Input, Output
from sqlalchemy import create_engine

# --- 1. Path & Credential Configuration ---
# Finds .env in the project root (one level up from this /dash_app folder)
root_dir = Path(__file__).resolve().parent.parent
dotenv_path = root_dir / '.env'

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Fail-Fast Validation: Ensure required variables are set
REQUIRED_VARS = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']
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

engine_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(engine_url)

series_mapping = {
    'WPU091503': 'PPI: Corrugated Boxes',
    'PCU331110331110': 'PPI: Iron and Steel Mills',
    'PCU484121484121': 'PPI: General Freight Trucking'
}

# --- 2. Initialize Dash App ---
app = dash.Dash(__name__)

# --- 3. Dashboard Layout ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '30px', 'backgroundColor': '#f4f6f9'}, children=[
    html.H1("Supply Chain Commodity Analytics", style={'textAlign': 'center', 'color': '#2c3e50'}),
    dcc.Dropdown(
        id='commodity-dropdown', 
        options=[{'label': name, 'value': sid} for sid, name in series_mapping.items()], 
        value='WPU091503', 
        clearable=False,
        style={'width': '50%', 'margin': '0 auto'}
    ),
    html.Div(id='kpi-card', style={
        'textAlign': 'center', 'fontSize': '22px', 'fontWeight': 'bold', 
        'color': '#2980b9', 'margin': '30px'
    }),
    html.Div([
        dcc.Graph(id='trend-chart'), 
        dcc.Graph(id='yearly-avg-chart')
    ])
])

# --- 4. Interactivity ---
@app.callback(
    [Output('kpi-card', 'children'), 
     Output('trend-chart', 'figure'), 
     Output('yearly-avg-chart', 'figure')],
    [Input('commodity-dropdown', 'value')]
)
def update_dashboard(selected_series):
    query = f"SELECT * FROM fact_observations WHERE series_id = '{selected_series}' ORDER BY observation_date"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        return "No data found for this series.", {}, {}
    
    latest_record = df.iloc[-1]
    kpi_text = f"Latest Value ({latest_record['observation_date'].strftime('%b %Y')}): {latest_record['value']}"
    
    fig_trend = px.line(df, x='observation_date', y='value', title=f"{series_mapping[selected_series]} Trend")
    fig_trend.update_layout(template='plotly_white')
    
    yearly_avg = df.groupby('observation_year')['value'].mean().reset_index()
    fig_bar = px.bar(yearly_avg, x='observation_year', y='value', title=f"{series_mapping[selected_series]} Annual Avg")
    fig_bar.update_layout(template='plotly_white')
    
    return kpi_text, fig_trend, fig_bar

if __name__ == '__main__':
    app.run_server(debug=True)