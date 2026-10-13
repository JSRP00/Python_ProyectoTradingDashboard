import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import krakenex
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import webbrowser

# Clases para manejar datos y cálculos
class KrakenData:
    def __init__(self):
        self.api = krakenex.API()

    def fetch_asset_pairs(self):
        try:
            response = self.api.query_public('AssetPairs')
            if 'result' not in response:
                raise ValueError("No result field in Kraken API response.")
            pairs = list(response['result'].keys())
            formatted_pairs = [f"{pair[:3]}/{pair[3:]}" for pair in pairs]
            return formatted_pairs
        except Exception as e:
            print(f"Error fetching asset pairs: {e}")
            return []

    def fetch_data(self, pair, interval):
        try:
            response = self.api.query_public('OHLC', {'pair': pair, 'interval': interval})
            if 'error' in response and response['error']:
                raise ValueError(f"Error from Kraken API: {response['error']}")
            data = response['result'][list(response['result'].keys())[0]]
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            return df
        except KeyError as e:
            print(f"KeyError: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

# Inicializar KrakenData y obtener los pares de activos
kraken_data = KrakenData()
asset_pairs = kraken_data.fetch_asset_pairs()

# Mostrar advertencia si no hay pares disponibles
if not asset_pairs:
    print("No se pudieron obtener pares de activos de la API de Kraken. Revisa tu conexión o credenciales.")

# Añadimos nuevos cálculos en IndicatorCalculator
class IndicatorCalculator:
    @staticmethod
    def calculate_bollinger_bands(df, window=20):
        if len(df) < window:
            raise ValueError("Not enough data points to calculate Bollinger Bands.")
        df['mean'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper_band'] = df['mean'] + 2 * df['std']
        df['lower_band'] = df['mean'] - 2 * df['std']
        df['buy_signal'] = np.where(df['close'] < df['lower_band'], df['close'], np.nan)
        df['sell_signal'] = np.where(df['close'] > df['upper_band'], df['close'], np.nan)
        return df

    @staticmethod
    def calculate_rsi(df, window=14):
        delta = df['close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=window, min_periods=1).mean()
        avg_loss = pd.Series(loss).rolling(window=window, min_periods=1).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
        df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        df['macd'] = df['ema_fast'] - df['ema_slow']
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
        return df

calculator = IndicatorCalculator()

# Actualizamos la lista de opciones de indicadores en el layout

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
            html.Div([
                html.Button("1D", id="1d-button", n_clicks=0, className="btn btn-dark mr-1"),
                html.Button("1W", id="1w-button", n_clicks=0, className="btn btn-dark mr-1"),
                html.Button("1M", id="1m-button", n_clicks=0, className="btn btn-dark mr-1"),
            ], className="mb-3"),
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
            html.Div(id="volume-info", className="mt-3 text-white"),
            html.Div(id="change-info", className="mt-3 text-white"),
            html.Div(id="signals-info", className="mt-3 text-white"),
        ], width=3),
        dbc.Col([
            dcc.Graph(id="main-chart", style={"height": "80vh"}),
        ], width=9),
    ]),
], fluid=True)

@app.callback(
    [Output("main-chart", "figure"),
     Output("current-price", "children"),
     Output("volume-info", "children"),
     Output("change-info", "children"),
     Output("signals-info", "children")],
    [Input("pair-dropdown", "value"),
     Input("chart-options", "value"),
     Input("bollinger-window", "value"),
     Input("1d-button", "n_clicks"),
     Input("1w-button", "n_clicks"),
     Input("1m-button", "n_clicks")]
)
def update_charts(pair, selected_charts, bollinger_window, n1d, n1w, n1m):
    try:
        if not pair:
            return go.Figure(), "Current Price: -", "Volume (24h): -", "Change (24h): -", "Signals: -"

        interval = None
        ctx = dash.callback_context
        if ctx.triggered:
            prop_id = ctx.triggered[0]['prop_id']
            if "1d-button" in prop_id:
                interval = '1D'
            elif "1w-button" in prop_id:
                interval = '1W'
            elif "1m-button" in prop_id:
                interval = '1M'

        df = kraken_data.fetch_data(pair, 5) # Fetch all data by using a shorter interval and then aggregating
        if df is None or df.empty:
            raise ValueError("No data returned for the selected pair and interval.")

        df = df[df['volume'] > 0]

        if interval == '1D':
            start_date = df['time'].max() - pd.Timedelta(days=1)
        elif interval == '1W':
            start_date = df['time'].max() - pd.Timedelta(weeks=1)
        elif interval == '1M':
            start_date = df['time'].max() - pd.DateOffset(months=1)
        else:
            start_date = df['time'].min()

        df = df[df['time'] >= start_date]

        if "bollinger" in selected_charts:
            df = calculator.calculate_bollinger_bands(df, window=bollinger_window)
        if "rsi" in selected_charts:
            df = calculator.calculate_rsi(df)
        if "macd" in selected_charts:
            df = calculator.calculate_macd(df)

        # Asegurar que los datos están ordenados cronológicamente
        df = df.sort_values(by='time', ascending=True)

        fig = go.Figure()
        fig.update_layout(template="plotly_dark")

        fig.add_trace(go.Candlestick(
            x=df['time'],
            open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            name="Candlesticks"
        ))

        if "bollinger" in selected_charts:
            fig.add_trace(go.Scatter(x=df['time'], y=df['upper_band'], mode='lines', name='Upper Band'))
            fig.add_trace(go.Scatter(x=df['time'], y=df['lower_band'], mode='lines', name='Lower Band'))
            fig.add_trace(go.Scatter(x=df['time'], y=df['buy_signal'], mode='markers', name='Buy Signal', marker=dict(color='green', size=10, symbol='triangle-up')))
            fig.add_trace(go.Scatter(x=df['time'], y=df['sell_signal'], mode='markers', name='Sell Signal', marker=dict(color='red', size=10, symbol='triangle-down')))

        if "rsi" in selected_charts:
            fig.add_trace(go.Scatter(x=df['time'], y=df['rsi'], mode='lines', name='RSI', line=dict(color='purple')))

        if "macd" in selected_charts:
            fig.add_trace(go.Scatter(x=df['time'], y=df['macd'], mode='lines', name='MACD', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df['time'], y=df['macd_signal'], mode='lines', name='MACD Signal', line=dict(color='orange')))

        # Ajustar los ejes del gráfico según el intervalo seleccionado
        end_date = df['time'].max()
        fig.update_xaxes(range=[start_date, end_date])

        fig.update_xaxes(rangeslider_visible=True)

        current_price = f"Current Price: {df['close'].iloc[-1]:.2f}"
        volume_info = f"Volume (24h): {df['volume'].sum():.2f}"
        change_info = f"Change (24h): {((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100):.2f}%"
        signals_info = f"Buy Signals: {df['buy_signal'].notna().sum()}, Sell Signals: {df['sell_signal'].notna().sum()}"

        fig.update_layout(
            title="Selected Indicators",
            xaxis_title="Time",
            yaxis_title="Price / Indicator Values",
            template="plotly_dark",
            font=dict(
                color="white",
                size=12,
            ),
            xaxis=dict(
                tickfont=dict(
                    color="white"
                ),
                titlefont=dict(
                    color="white"
                )
            ),
            yaxis=dict(
                tickfont=dict(
                    color="white"
                ),
                titlefont=dict(
                    color="white"
                )
            )
        )

        return fig, current_price, volume_info, change_info, signals_info

    except Exception as e:
        print(f"Callback error: {e}")
        return go.Figure(), "Error: Unable to generate chart.", "-", "-", "-"

if __name__ == "__main__":
    webbrowser.open_new("http://127.0.0.1:8050/")
    app.run(debug=True)
 