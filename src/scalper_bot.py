import time
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector, TradingStrategy

class MicroScalperBot:
    def __init__(self, symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "LINKUSDT"], initial_balance=1000, duration_minutes=60):
        self.symbols = symbols
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.active_symbol = None
        self.position = 0
        self.duration_minutes = duration_minutes
        self.trades = []
        self.results_dir = "scalper_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Window for calculating 2nd highest/lowest
        self.window_size = 15

    def log_trade(self, action, symbol, price, timestamp):
        trade = {
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "symbol": symbol,
            "action": action,
            "price": price,
            "balance": self.balance,
            "position": self.position,
            "total_value": self.balance + (self.position * price)
        }
        self.trades.append(trade)
        pd.DataFrame(self.trades).to_csv(f"{self.results_dir}/trade_history.csv", index=False)
        with open(f"{self.results_dir}/status.json", "w") as f:
            json.dump(trade, f, indent=4)

    def run(self):
        print(f"⚡ [SCALPER BOT] Starting 1-hour Micro-Scalping session...")
        print(f"Strategy: Buy @ 2nd Lowest | Sell @ 2nd Highest")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.duration_minutes)
        iteration = 1
        detector = FraudDetector()
        
        while datetime.now() < end_time:
            print(f"\n⏱️ [Scalp Tick {iteration}] {datetime.now().strftime('%H:%M:%S')}")
            
            # Scan assets
            for sym in (self.symbols if not self.active_symbol else [self.active_symbol]):
                df = fetch_live_crypto_data(symbol=sym, interval="1m", limit=50)
                if df is None or len(df) < self.window_size: continue
                
                # Self-Training update
                processed_df = detector.prepare_features(df)
                detector.train(processed_df)
                
                prices = sorted(df['price'].tolist())
                second_lowest = prices[1]
                second_highest = prices[-2]
                current_price = df.iloc[-1]['price']
                current_time = df.iloc[-1]['timestamp']
                
                # Logic: BUY if price is at or below the 2nd lowest point of the window
                if not self.active_symbol and current_price <= second_lowest:
                    self.active_symbol = sym
                    self.position = self.balance / current_price
                    self.balance = 0
                    print(f"💎 SCALP BUY: {sym} @ ${current_price:,.4f} (2nd Lowest: ${second_lowest:,.4f})")
                    self.log_trade("BUY", sym, current_price, current_time)
                    break
                
                # Logic: SELL if price is at or above the 2nd highest point of the window
                elif self.active_symbol == sym and current_price >= second_highest:
                    self.balance = self.position * current_price
                    print(f"💰 SCALP SELL: {sym} @ ${current_price:,.4f} (2nd Highest: ${second_highest:,.4f})")
                    self.position = 0
                    self.log_trade("SELL", sym, current_price, current_time)
                    self.active_symbol = None
                    break
            
            # Update Status
            val = self.balance
            if self.active_symbol:
                curr_df = fetch_live_crypto_data(symbol=self.active_symbol, limit=1)
                val += self.position * curr_df.iloc[-1]['price']
            
            with open(f"{self.results_dir}/status.json", "w") as f:
                json.dump({
                    "timestamp": datetime.now().strftime('%H:%M:%S'),
                    "active_asset": self.active_symbol or "None (Scanning...)",
                    "balance": self.balance,
                    "total_value": val
                }, f, indent=4)

            iteration += 1
            time.sleep(60)

        # Settlement
        print("\n🏁 [SCALP SESSION ENDED]")
        if self.active_symbol:
            df_final = fetch_live_crypto_data(symbol=self.active_symbol, limit=1)
            self.balance = self.position * df_final.iloc[-1]['price']
            
        print(f"Final Scalper Balance: ${self.balance:,.2f}")

if __name__ == "__main__":
    bot = MicroScalperBot()
    bot.run()
