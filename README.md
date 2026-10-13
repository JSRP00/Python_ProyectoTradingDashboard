# Trading Dashboard

Interactive dashboard for cryptocurrency pairs, built with Dash on live market data from the public Kraken API. Course project for *Python for Data Analysis* (MSc in Big Data Science, University of Navarra, 2024).

## Features

- Downloads OHLC price data for any Kraken asset pair (`krakenex`)
- Technical indicators implemented from scratch: Bollinger Bands, RSI and MACD
- Interactive candlestick charts with buy and sell signals (Plotly, Dash)
- Unit tests for data retrieval and indicator calculations

## Structure

| File | Purpose |
| --- | --- |
| `main.py` | Dash app and callbacks |
| `kraken_data.py` | Kraken API client |
| `indicator_calculator.py` | Bollinger Bands, RSI and MACD |
| `Test_ProyectoTradingDashboard.py` | Unit tests |
| `MemoriaTradingDashboard.pdf` | Project report (Spanish) |

## Run it

```bash
git clone https://github.com/JSRP00/Python_ProyectoTradingDashboard.git
cd Python_ProyectoTradingDashboard
pip install -r requirements.txt
python main.py
```

The app opens in the browser. Tests: `pytest Test_ProyectoTradingDashboard.py` (the data tests call the Kraken API and need internet access).
