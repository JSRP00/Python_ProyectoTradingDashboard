import unittest
from ProyectoTradingDashboard import KrakenData, IndicatorCalculator
import pandas as pd

class TestKrakenData(unittest.TestCase):

    def setUp(self):
        self.kraken_data = KrakenData()

    def test_fetch_asset_pairs(self):
        pairs = self.kraken_data.fetch_asset_pairs()
        self.assertIsInstance(pairs, list, "The result should be a list of asset pairs.")
        self.assertGreater(len(pairs), 0, "The list of asset pairs should not be empty.")

    def test_fetch_data(self):
        df = self.kraken_data.fetch_data('ETHUSD', 1440)
        self.assertIsInstance(df, pd.DataFrame, "The result should be a pandas DataFrame.")
        self.assertFalse(df.empty, "The DataFrame should not be empty.")

class TestIndicatorCalculator(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            'close': [100, 102, 101, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87]
        })

    def test_calculate_bollinger_bands(self):
        df = IndicatorCalculator.calculate_bollinger_bands(self.df, window=5)
        self.assertIn('upper_band', df, "The DataFrame should contain 'upper_band'.")
        self.assertIn('lower_band', df, "The DataFrame should contain 'lower_band'.")
        self.assertIn('buy_signal', df, "The DataFrame should contain 'buy_signal'.")
        self.assertIn('sell_signal', df, "The DataFrame should contain 'sell_signal'.")

    def test_calculate_rsi(self):
        df = IndicatorCalculator.calculate_rsi(self.df, window=5)
        self.assertIn('rsi', df, "The DataFrame should contain 'rsi'.")

    def test_calculate_macd(self):
        df = IndicatorCalculator.calculate_macd(self.df, fast_period=5, slow_period=10, signal_period=3)
        self.assertIn('macd', df, "The DataFrame should contain 'macd'.")
        self.assertIn('macd_signal', df, "The DataFrame should contain 'macd_signal'.")

