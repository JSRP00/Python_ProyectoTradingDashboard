import krakenex
import pandas as pd

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