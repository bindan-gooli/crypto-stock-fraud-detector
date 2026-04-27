import pandas as pd
from src.live_ingestion import fetch_live_crypto_data

def check_scalper_targets():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "LINKUSDT"]
    window_size = 15
    
    print(f"🎯 [TARGET SCAN] Calculating 'Second-Best' Targets (Window: {window_size}m)")
    print("-" * 65)
    print(f"{'Symbol':<10} | {'Current':<12} | {'2nd Lowest':<12} | {'2nd Highest':<12}")
    print("-" * 65)
    
    for sym in symbols:
        df = fetch_live_crypto_data(symbol=sym, interval="1m", limit=window_size + 1)
        if df is not None and len(df) >= window_size:
            prices = sorted(df['price'].tolist())
            current = df.iloc[-1]['price']
            second_lowest = prices[1]
            second_highest = prices[-2]
            
            status = " "
            if current <= second_lowest: status = "🟢 BUY ZONE"
            if current >= second_highest: status = "🔴 SELL ZONE"
            
            print(f"{sym:<10} | ${current:<10.2f} | ${second_lowest:<10.2f} | ${second_highest:<10.2f} {status}")
        else:
            print(f"{sym:<10} | Data Unavailable")

if __name__ == "__main__":
    check_scalper_targets()
