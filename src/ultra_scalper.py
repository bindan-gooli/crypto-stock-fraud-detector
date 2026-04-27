import time
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector

class UltraScalperBot:
    def __init__(self, symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "LINKUSDT"], initial_balance=1003.24, duration_minutes=60):
        self.symbols = symbols
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}
        self.max_slots = 5
        self.slot_size = initial_balance / self.max_slots
        self.duration_minutes = duration_minutes
        self.trades = []
        self.results_dir = "ultra_scalp_results"
        os.makedirs(self.results_dir, exist_ok=True)
        self.window_size = 3

    def log_trade(self, action, symbol, price, timestamp):
        trade = {
            "timestamp": timestamp.strftime('%H:%M:%S'),
            "symbol": symbol,
            "action": action,
            "price": price,
            "balance": self.balance,
            "total_value": self.get_total_value()
        }
        self.trades.append(trade)
        pd.DataFrame(self.trades).to_csv(f"{self.results_dir}/trade_history.csv", index=False)
        with open(f"{self.results_dir}/status.json", "w") as f:
            json.dump({
                "time": timestamp.strftime('%H:%M:%S'),
                "active_positions": list(self.positions.keys()),
                "balance": self.balance,
                "total_value": self.get_total_value(),
                "trades_done": len(self.trades)
            }, f, indent=4)

    def get_total_value(self):
        val = self.balance
        for sym, pos in self.positions.items():
            val += pos["units"] * pos["entry_price"]
        return val

    def run(self):
        print(f"🚀 [ULTRA-SCALPER] Starting 30+ trade/hour marathon...")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.duration_minutes)
        detector = FraudDetector()
        
        iteration = 1
        while datetime.now() < end_time:
            for sym in self.symbols:
                # Fetch 100 points for stable training, but scalp on the last 3
                df = fetch_live_crypto_data(symbol=sym, interval="1m", limit=100)
                if df is None or len(df) < 20: continue
                
                # Safe Training
                try:
                    processed_df = detector.prepare_features(df)
                    if len(processed_df) > 10:
                        detector.train(processed_df)
                except Exception as e:
                    print(f"⚠️ Training skip for {sym}: {e}")
                
                # Scalp Logic on the micro window
                micro_df = df.iloc[-self.window_size:]
                prices = sorted(df['price'].iloc[-15:].tolist()) # 15 min window for 2nd best calculation
                second_lowest = prices[1]
                second_highest = prices[-2]
                current_price = df.iloc[-1]['price']
                
                # SELL
                if sym in self.positions and current_price >= second_highest:
                    units = self.positions[sym]["units"]
                    self.balance += units * current_price
                    del self.positions[sym]
                    print(f"💰 [SELL] {sym} @ ${current_price:.4f} | Trades: {len(self.trades)+1}")
                    self.log_trade("SELL", sym, current_price, datetime.now())

                # BUY
                elif sym not in self.positions and len(self.positions) < self.max_slots and current_price <= second_lowest:
                    if self.balance >= self.slot_size:
                        units = self.slot_size / current_price
                        self.balance -= self.slot_size
                        self.positions[sym] = {"units": units, "entry_price": current_price}
                        print(f"💎 [BUY] {sym} @ ${current_price:.4f} | Slots: {len(self.positions)}")
                        self.log_trade("BUY", sym, current_price, datetime.now())

            iteration += 1
            time.sleep(10)

if __name__ == "__main__":
    bot = UltraScalperBot()
    bot.run()
