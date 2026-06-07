import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# --- 1. Database Connectivity ---
DB_USER = 'YOUR_USERNAME_HERE'
DB_PASSWORD = 'YOUR_PASSWORD_HERE'
DB_HOST = 'YOUR_HOSTNAME_HERE' 
DB_PORT = 'YOUR_PORT_HERE'
DB_NAME = 'YOUR_DB_NAME_HERE'

engine_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(engine_url)

# Reference mapping for the dropdown filter
series_mapping = {
    'WPU091503': 'PPI: Corrugated Boxes',
    'PCU331110331110': 'PPI: Iron and Steel Mills',
    'PCU484121484121': 'PPI: General Freight Trucking'
}

# --- Initialize Dash App ---
app = dash.Dash(__name__)

# --- 2. Dashboard Components & Layout ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '30px', 'backgroundColor': '#f4f6f9'}, children=[
    
    html.H1("Supply Chain Commodity Analytics", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.P("Interactive dashboard monitoring raw material and logistics pricing trends.", style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),
    
    # Interactive Filter
    html.Div([
        html.Label("Select Commodity Series:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='commodity-dropdown',
            options=[{'label': name, 'value': sid} for sid, name in series_mapping.items()],
            value='WPU091503', # Default selected value
            clearable=False,
            style={'width': '300px', 'display': 'inline-block', 'verticalAlign': 'middle'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    # KPI Summary Metric Card
    html.Div(id='kpi-card', style={
        'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 
        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'textAlign': 'center', 
        'fontSize': '22px', 'fontWeight': 'bold', 'color': '#2980b9', 'marginBottom': '30px'
    }),
    
    # 2 Visualizations (Time-Series and Annual Averages)
    html.Div([
        dcc.Graph(id='trend-chart', style={'display': 'inline-block', 'width': '49%', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        dcc.Graph(id='yearly-avg-chart', style={'display': 'inline-block', 'width': '49%', 'float': 'right', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'})
    ])
])

# --- 3. Interactivity (Callbacks) ---
@app.callback(
    [Output('kpi-card', 'children'),
     Output('trend-chart', 'figure'),
     Output('yearly-avg-chart', 'figure')],
    [Input('commodity-dropdown', 'value')]
)
def update_dashboard(selected_series):
    # Pull refreshed data using efficient SQL queries matching the chosen dropdown item
    query = f"SELECT * FROM fact_observations WHERE series_id = '{selected_series}' ORDER BY observation_date"
    df = pd.read_sql(query, engine)
    
    commodity_name = series_mapping[selected_series]
    
    # KPI Calculation
    latest_record = df.iloc[-1]
    latest_date = latest_record['observation_date'].strftime('%b %Y')
    latest_value = latest_record['value']
    kpi_text = f"Latest Index Value ({latest_date}): {latest_value}"
    
    # Visualization 1: Time Series Trend Line
    fig_trend = px.line(df, x='observation_date', y='value', 
                        title=f"{commodity_name} - Historical Trend",
                        labels={'observation_date': 'Date', 'value': 'Index Value'})
    fig_trend.update_layout(template='plotly_white', margin=dict(l=40, r=40, t=50, b=40))
    
    # Visualization 2: Annual Average Bar Chart
    yearly_avg = df.groupby('observation_year')['value'].mean().reset_index()
    fig_bar = px.bar(yearly_avg, x='observation_year', y='value', 
                     title=f"{commodity_name} - Annual Average",
                     labels={'observation_year': 'Year', 'value': 'Average Index Value'})
    fig_bar.update_layout(template='plotly_white', margin=dict(l=40, r=40, t=50, b=40))
    
    return kpi_text, fig_trend, fig_bar

# --- Execution ---
if __name__ == '__main__':
    app.run_server(debug=True)
