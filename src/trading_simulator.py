import pandas as pd
import numpy as np
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector, TradingStrategy
from src.data_generator import generate_crypto_data
from datetime import datetime, timedelta
import os

def simulate_20_min_trading(symbol="BTCUSDT", initial_balance=1000):
    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(msg)

    log(f"💰 Starting 20-Minute Trading Simulation for {symbol}...")
    
    # 1. Fetch 1-minute data for the last 60 minutes
    df = fetch_live_crypto_data(symbol=symbol, interval="1m", limit=60)
    if df is None or len(df) < 20:
        log("Insufficient data for simulation.")
        return

    # 2. Prepare & Train Model (Bootstrap with Synthetic Data)
    log("Training base model on synthetic data...")
    train_df = generate_crypto_data(n_points=2000)
    detector = FraudDetector()
    train_processed = detector.prepare_features(train_df)
    detector.train(train_processed)
    
    # Predict on the last 20 minutes of live data
    processed_df = detector.prepare_features(df).copy()
    test_df = processed_df.iloc[-20:].copy()
    
    probs = detector.predict(test_df)
    test_df['fraud_prob'] = probs
    
    strategy = TradingStrategy()
    test_df['signal'] = strategy.generate_signals(test_df)
    
    # 3. Simulate Trading
    balance = initial_balance
    position = 0 
    trades_count = 0
    
    log("\n--- TRADE LOG ---")
    for i in range(len(test_df)):
        row = test_df.iloc[i]
        time_str = row['timestamp'].strftime('%H:%M:%S')
        price = row['price']
        signal = row['signal']
        
        if signal == "BUY" and balance > 0:
            position = balance / price
            balance = 0
            trades_count += 1
            log(f"[{time_str}] BUY {symbol} @ ${price:,.2f} | Balance: ${balance:.2f} | Holdings: {position:.6f}")
            
        elif signal == "SELL" and position > 0:
            balance = position * price
            position = 0
            trades_count += 1
            log(f"[{time_str}] SELL {symbol} @ ${price:,.2f} | Balance: ${balance:.2f} | Holdings: {position:.6f}")
            
    # Final settlement
    if position > 0:
        final_price = test_df.iloc[-1]['price']
        balance = position * final_price
        log(f"[{test_df.iloc[-1]['timestamp'].strftime('%H:%M:%S')}] FINAL SETTLE @ ${final_price:,.2f} | Balance: ${balance:.2f}")
        
    profit_loss = balance - initial_balance
    log(f"\n--- SIMULATION SUMMARY ---")
    log(f"Initial Balance: ${initial_balance:.2f}")
    log(f"Final Balance:   ${balance:.2f}")
    log(f"Trades Executed: {trades_count}")
    log(f"Profit/Loss:     ${profit_loss:.2f} ({profit_loss/initial_balance*100:.2f}%)")
    
    # Save results to folder
    os.makedirs("trading_sim_results", exist_ok=True)
    with open("trading_sim_results/sim_report.txt", "w") as f:
        f.write("\n".join(output_lines))
    
    return balance

if __name__ == "__main__":
    simulate_20_min_trading()
