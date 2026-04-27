import time
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector, TradingStrategy

class LiveTradingBot:
    def __init__(self, symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"], initial_balance=1000, duration_minutes=60):
        self.symbols = symbols
        self.active_symbol = None
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.position = 0 # Holdings in crypto
        self.duration_minutes = duration_minutes
        self.trades = []
        self.results_dir = "live_trading_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load optimized strategy if exists
        config_path = "models/trading_config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                params = json.load(f)
            self.strategy = TradingStrategy(**params)
            print(f"Loaded optimized strategy: {params}")
        else:
            self.strategy = TradingStrategy()
            print("Using default strategy.")

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
        # Save history to CSV
        pd.DataFrame(self.trades).to_csv(f"{self.results_dir}/trade_history.csv", index=False)
        # Save current status
        with open(f"{self.results_dir}/status.json", "w") as f:
            json.dump(trade, f, indent=4)

    def run(self):
        print(f"🚀 [LIVE BOT] Starting 1-hour live session scanning: {self.symbols}...")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=self.duration_minutes)
        
        iteration = 1
        detector = FraudDetector()
        
        while datetime.now() < end_time:
            print(f"\n⏱️ [Tick {iteration}] {datetime.now().strftime('%H:%M:%S')}")
            
            best_opportunity = None
            
            # If we already have a position, we only care about that symbol's SELL signal
            if self.active_symbol:
                scan_list = [self.active_symbol]
            else:
                scan_list = self.symbols

            for sym in scan_list:
                df = fetch_live_crypto_data(symbol=sym, interval="1m", limit=100)
                if df is None: continue
                
                processed_df = detector.prepare_features(df)
                detector.train(processed_df)
                
                probs = detector.predict(processed_df)
                processed_df['fraud_prob'] = probs
                
                signals = self.strategy.generate_signals(processed_df)
                current_signal = signals[-1]
                current_price = processed_df.iloc[-1]['price']
                current_time = processed_df.iloc[-1]['timestamp']
                
                # Check for SELL if holding
                if self.active_symbol and current_signal == "SELL":
                    self.balance = self.position * current_price
                    print(f"🔥 EXECUTE SELL: {self.active_symbol} | ${self.balance:,.2f} returned @ ${current_price:,.2f}")
                    self.log_trade("SELL", self.active_symbol, current_price, current_time)
                    self.position = 0
                    self.active_symbol = None
                    break
                
                # Check for BUY if not holding
                if not self.active_symbol and current_signal == "BUY":
                    # Simple heuristic: pick the first BUY found in this tick
                    self.active_symbol = sym
                    self.position = self.balance / current_price
                    self.balance = 0
                    print(f"✅ EXECUTE BUY: {sym} | {self.position:.6f} units @ ${current_price:,.2f}")
                    self.log_trade("BUY", sym, current_price, current_time)
                    break
            
            # Log Status
            with open(f"{self.results_dir}/status.json", "w") as f:
                val = self.balance
                if self.active_symbol:
                    # Need price for total value
                    curr_df = fetch_live_crypto_data(symbol=self.active_symbol, limit=1)
                    val += self.position * curr_df.iloc[-1]['price']
                
                status = {
                    "timestamp": datetime.now().strftime('%H:%M:%S'),
                    "active_asset": self.active_symbol or "None (Scanning...)",
                    "balance": self.balance,
                    "holdings": self.position,
                    "total_value": val
                }
                json.dump(status, f, indent=4)

            iteration += 1
            time.sleep(60)
            
        # Final Settlement
        print("\n🏁 [SESSION ENDED] Calculating final results...")
        if self.active_symbol:
            df_final = fetch_live_crypto_data(symbol=self.active_symbol, limit=1)
            final_price = df_final.iloc[-1]['price']
            self.balance = self.position * final_price
        
        report = {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "profit_loss": self.balance - self.initial_balance,
            "roi_percent": ((self.balance - self.initial_balance) / self.initial_balance) * 100,
            "total_trades": len(self.trades)
        }
        
        with open(f"{self.results_dir}/final_report.json", "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"🏆 Final Wallet Balance: ${final_value:,.2f}")

if __name__ == "__main__":
    bot = LiveTradingBot()
    bot.run()
