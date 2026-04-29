#  Crypto Guard: Hybrid Fraud Detector & Ultra-Scalper

A high-impact, real-time intelligence system designed to identify market manipulation and execute high-precision algorithmic trades. This project combines **Anomaly Detection** with **Micro-Scalping** strategies to provide a secure and profitable trading environment.

##  Key Features

### 1. Hybrid Fraud Detection
- **Self-Supervised Learning**: Uses Isolation Forest and XGBoost to identify fraudulent spikes and wash trading in real-time without needing pre-labeled data.
- **Anomaly Detection**: Filters out high-risk trades by analyzing volume/price divergence.

### 2. Ultra-Scalper Bot (30+ Trades/Hour)
- **Wait & Confirm Strategy**: Specifically designed to buy at the **Second-Lowest** price point and sell at the **Second-Highest**, avoiding "falling knives" and "top-tick" reversals.
- **Multi-Position Engine**: Manages up to 5 simultaneous positions across a diversified list of high-volatility assets (DOGE, PEPE, SHIB, LINK, etc.).
- **Aggressive Polling**: 10-second polling intervals for maximum capture of micro-volatility.

### 3. Live Intelligence Dashboard
- **Real-Time P/L Tracking**: Monitor your wallet balance and active positions live.
- **Live Candlestick Charts**: High-resolution charts with Bollinger Bands and RSI overlays.
- **Execution Logs**: Instant feedback on every Buy, Sell, and Hold decision.

##  Tech Stack

- **Core**: Python 3.13+
- **ML Frameworks**: Scikit-learn, XGBoost, PyTorch (LSTM Autoencoders)
- **Data**: Pandas, NumPy, Binance API
- **Frontend**: Streamlit, Plotly
- **Infrastructure**: Docker, GitHub Actions

##  Getting Started

###  Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/vinodsakh/crypto-stock-fraud-detector.git
   cd crypto-stock-fraud-detector
   ```

2. **Set up environment & Install dependencies**:
   ```bash
   bash setup_project.sh
   ```

###  Execution
Using the included **Makefile**:
- **Start Scalper**: `make scalp`
- **Start Dashboard**: `make dashboard`
- **Check Targets**: `make targets`

##  Project Structure
- `src/ultra_scalper.py`: The high-frequency trading engine.
- `src/bot_dashboard.py`: The Streamlit-based monitoring frontend.
- `src/model.py`: Hybrid ML models for anomaly and fraud detection.
- `src/live_ingestion.py`: Real-time exchange data fetcher.




**Created by**: [bindan-gooli](https://github.com/bindan-gooli)
