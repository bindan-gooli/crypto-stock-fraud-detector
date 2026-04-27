import pandas as pd
import numpy as np
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector, TradingStrategy
from datetime import datetime

def run_backtest(symbol="BTCUSDT", limit=500):
    print(f"📊 Running Backtest for {symbol} (Last {limit} periods)...")
    
    # 1. Fetch historical data
    df = fetch_live_crypto_data(symbol=symbol, limit=limit)
    if df is None:
        print("Failed to fetch data.")
        return

    # 2. Prepare & Train Model (Bootstrap with Synthetic Data)
    print("Training base model on synthetic data...")
    from src.data_generator import generate_crypto_data
    train_df = generate_crypto_data(n_points=2000)
    detector = FraudDetector()
    train_processed = detector.prepare_features(train_df)
    detector.train(train_processed)
    
    # Process test data (Live Market)
    test_df = detector.prepare_features(df).copy()
    
    probs = detector.predict(test_df)
    test_df['fraud_prob'] = probs
    
    strategy = TradingStrategy()
    test_df['signal'] = strategy.generate_signals(test_df)
    
    # 3. Evaluate Signals
    # Let's see if the price increases 3 periods after a BUY signal
    look_ahead = 3
    test_df['future_price'] = test_df['price'].shift(-look_ahead)
    test_df['price_change'] = (test_df['future_price'] - test_df['price']) / test_df['price']
    
    buy_signals = test_df[test_df['signal'] == "BUY"]
    sell_signals = test_df[test_df['signal'] == "SELL"]
    
    print(f"\n--- BACKTEST RESULTS ({symbol}) ---")
    print(f"Total Periods: {len(test_df)}")
    print(f"BUY Signals:   {len(buy_signals)}")
    print(f"SELL Signals:  {len(sell_signals)}")
    
    if len(buy_signals) > 0:
        win_rate = (buy_signals['price_change'] > 0).mean()
        avg_return = buy_signals['price_change'].mean()
        print(f"BUY Win Rate:  {win_rate*100:.1f}%")
        print(f"Avg BUY Return: {avg_return*100:.2f}% (after {look_ahead} periods)")
    
    if len(sell_signals) > 0:
        win_rate = (sell_signals['price_change'] < 0).mean()
        avg_return = sell_signals['price_change'].mean()
        print(f"SELL Win Rate: {win_rate*100:.1f}%")
        print(f"Avg SELL Return: {avg_return*100:.2f}% (drop after {look_ahead} periods)")

    return test_df

if __name__ == "__main__":
    run_backtest()
