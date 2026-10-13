import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import webbrowser
from kraken_data import KrakenData
from indicator_calculator import IndicatorCalculator
import plotly.graph_objects as go

# Inicializar KrakenData
kraken_data = KrakenData()
asset_pairs = kraken_data.fetch_asset_pairs()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Trading Dashboard", className="text-center mb-4 text-white"),
            dcc.Dropdown(
                id="pair-dropdown",
                options=[{"label": pair, "value": pair.replace("/", "")} for pair in asset_pairs],
                placeholder="Select a pair",
                className="mb-3",
                style={"color": "black"}
            ),
            dcc.Checklist(
                id="chart-options",
                options=[
                    {"label": "Bollinger Bands", "value": "bollinger"},
                    {"label": "RSI", "value": "rsi"},
                    {"label": "MACD", "value": "macd"},
                ],
                value=["bollinger"],
                labelStyle={"display": "block", "color": "white"},
                className="mb-3"
            ),
            dbc.InputGroup([
                dbc.InputGroupText("Bollinger Bands Window"),
                dbc.Input(id="bollinger-window", type="number", value=20, min=1, className="mb-3"),
            ]),
            html.Div(id="current-price", className="mt-3 text-white"),
        ], width=3),
        dbc.Col([
            dcc.Graph(id="main-chart", style={"height": "80vh"}),
        ], width=9),
    ]),
], fluid=True)

@app.callback(
    [Output("main-chart", "figure"),
     Output("current-price", "children")],
    [Input("pair-dropdown", "value"),
     Input("chart-options", "value"),
     Input("bollinger-window", "value")]
)
def update_charts(pair, selected_charts, bollinger_window):
    try:
        if not pair:
            return go.Figure(), "Current Price: -"

        df = kraken_data.fetch_data(pair, 5)
        if df is None or df.empty:
            raise ValueError("No data returned for the selected pair and interval.")

        if "bollinger" in selected_charts:
            df = IndicatorCalculator.calculate_bollinger_bands(df, window=bollinger_window)
        if "rsi" in selected_charts:
            df = IndicatorCalculator.calculate_rsi(df)
        if "macd" in selected_charts:
            df = IndicatorCalculator.calculate_macd(df)

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df['time'],
            open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            name="Candlesticks"
        ))

        if "bollinger" in selected_charts:
            fig.add_trace(go.Scatter(x=df['time'], y=df['upper_band'], mode='lines', name='Upper Band'))
            fig.add_trace(go.Scatter(x=df['time'], y=df['lower_band'], mode='lines', name='Lower Band'))

        return fig, f"Current Price: {df['close'].iloc[-1]:.2f}"

    except Exception as e:
        print(f"Callback error: {e}")
        return go.Figure(), "Error: Unable to generate chart."

if __name__ == "__main__":
    webbrowser.open_new("http://127.0.0.1:8050/")
    app.run(debug=True)
