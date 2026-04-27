import requests
import pandas as pd
from datetime import datetime
import time

def fetch_live_crypto_data(symbol="BTCUSDT", interval="1h", limit=100):
    """
    Fetches real-time crypto data from Binance public API.
    """
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Binance kline format: [Open time, Open, High, Low, Close, Volume, Close time, ...]
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'number_of_trades', 
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['price'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['symbol'] = symbol
        
        return df[['timestamp', 'symbol', 'price', 'open', 'high', 'low', 'volume']]
    except Exception as e:
        print(f"Error fetching live data: {e}")
        return None

if __name__ == "__main__":
    print("Fetching live BTC/USDT data...")
    df = fetch_live_crypto_data()
    if df is not None:
        print(df.head())
        print(f"Fetched {len(df)} rows.")
