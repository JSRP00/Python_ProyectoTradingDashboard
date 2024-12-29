import numpy as np
import pandas as pd

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
