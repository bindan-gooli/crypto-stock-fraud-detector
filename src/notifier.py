import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        
    def send_discord_alert(self, symbol, price, risk_score, timestamp):
        """
        Sends a rich embed alert to a Discord channel.
        """
        if not self.webhook_url:
            print("⚠️ No Discord Webhook URL found. Skipping notification.")
            return

        payload = {
            "username": "Crypto Guard Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/2092/2092663.png",
            "embeds": [{
                "title": "🚨 FRAUD ALERT DETECTED",
                "color": 15548997, # Red
                "fields": [
                    {"name": "Symbol", "value": symbol, "inline": True},
                    {"name": "Price", "value": f"${price:,.2f}", "inline": True},
                    {"name": "Risk Score", "value": f"{risk_score*100:.1f}%", "inline": True},
                    {"name": "Timestamp", "value": timestamp.strftime('%Y-%m-%d %H:%M:%S'), "inline": False},
                ],
                "footer": {"text": "Powered by Antigravity AI"}
            }]
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            print(f"✅ Alert sent for {symbol}")
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")

    def log_alert(self, symbol, price, risk_score, timestamp):
        """
        Logs alert to a local file.
        """
        log_entry = {
            "symbol": symbol,
            "price": price,
            "risk_score": risk_score,
            "timestamp": timestamp.isoformat(),
            "type": "FRAUD_DETECTION"
        }
        
        os.makedirs("logs", exist_ok=True)
        with open("logs/alerts.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        print(f"📝 Alert logged locally for {symbol}")

if __name__ == "__main__":
    # Test notification
    notifier = Notifier()
    notifier.log_alert("BTC/USD", 65000.50, 0.95, datetime.now())
    # notifier.send_discord_alert("BTC/USD", 65000.50, 0.95, datetime.now()) # Requires env var
