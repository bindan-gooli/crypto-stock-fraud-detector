import pandas as pd
import numpy as np
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector, TradingStrategy
import json
import os

def optimize_model(symbol="BTCUSDT"):
    print(f"🚀 Starting Automated Model Optimization for {symbol}...")
    
    # 1. Fetch recent data (500 points of 1m data for training + optimization)
    df = fetch_live_crypto_data(symbol=symbol, interval="1m", limit=500)
    if df is None: return

    detector = FraudDetector()
    processed_df = detector.prepare_features(df).copy()
    
    # Train entirely on the live data (Self-Supervised)
    print("Training model on live market history...")
    detector.train(processed_df)
    
    processed_df['fraud_prob'] = detector.predict(processed_df)
    
    # 2. Parameter Grid Search
    best_profit = -float('inf')
    best_params = {}
    
    # Search space
    rsi_buys = [30, 35, 40]
    rsi_sells = [60, 65, 70]
    bb_mults = [1.0, 1.01, 1.02, 1.03]
    
    print("Searching for optimal parameters...")
    for rb in rsi_buys:
        for rs in rsi_sells:
            for bm in bb_mults:
                strategy = TradingStrategy(rsi_buy=rb, rsi_sell=rs, bb_mult=bm)
                signals = strategy.generate_signals(processed_df)
                
                # Simple profit calculation
                balance = 1000
                pos = 0
                for i in range(len(processed_df)):
                    p = processed_df.iloc[i]['price']
                    s = signals[i]
                    if s == "BUY" and balance > 0:
                        pos = balance / p
                        balance = 0
                    elif s == "SELL" and pos > 0:
                        balance = pos * p
                        pos = 0
                
                final_bal = balance if pos == 0 else pos * processed_df.iloc[-1]['price']
                profit = final_bal - 1000
                
                if profit > best_profit:
                    best_profit = profit
                    best_params = {'rsi_buy': rb, 'rsi_sell': rs, 'bb_mult': bm}

    print(f"✅ Optimization Complete. Best Profit Found: ${best_profit:.2f}")
    print(f"Best Parameters: {best_params}")
    
    # 3. Update Model config
    os.makedirs("models", exist_ok=True)
    with open("models/trading_config.json", "w") as f:
        json.dump(best_params, f)
    
    return best_params, best_profit

if __name__ == "__main__":
    optimize_model()
