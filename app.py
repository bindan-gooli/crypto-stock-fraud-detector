import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.data_generator import generate_crypto_data
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector, TradingStrategy
from src.deep_model import DeepFraudDetector
from src.notifier import Notifier
import time
import json
import os

# Page Config
st.set_page_config(
    page_title="Crypto Guard | Fraud Detection Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .fraud-alert {
        padding: 10px;
        background-color: rgba(255, 75, 75, 0.2);
        border-radius: 10px;
        border: 1px solid #ff4b4b;
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.title("🛡️ Crypto Guard: Real-Time Fraud Detector")
st.markdown("---")

# Sidebar
st.sidebar.title("Settings")
st.sidebar.info("Adjust detection sensitivity and data parameters.")

mode = st.sidebar.radio("Data Source", ["Synthetic", "Live Market"])
threshold = st.sidebar.slider("Detection Threshold (Probability)", 0.0, 1.0, 0.7)

if mode == "Synthetic":
    data_points = st.sidebar.number_input("Historical Data Points", 500, 5000, 1000)
else:
    symbol = st.sidebar.selectbox("Crypto Pair", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    data_points = 100

st.sidebar.markdown("---")
st.sidebar.subheader("Advanced Analysis")
use_deep_learning = st.sidebar.toggle("Enable LSTM Deep Learning", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("Notifications")
enable_logging = st.sidebar.checkbox("Log Alerts Locally", value=True)
webhook_url = st.sidebar.text_input("Discord Webhook URL", type="password")

if st.sidebar.button("Refresh Live Data"):
    st.rerun()

# Data Generation & Prediction
@st.cache_data(ttl=600)
def get_data(mode, n, symbol="BTCUSDT"):
    if mode == "Synthetic":
        df = generate_crypto_data(n_points=n)
    else:
        df = fetch_live_crypto_data(symbol=symbol, limit=n)
        if df is None:
            st.error("Failed to fetch live data.")
            return None
    
    detector = FraudDetector()
    
    # Bootstrap training on Live Data
    if mode == "Live Market":
        # Train on a larger window of live data to ensure model is calibrated to real market
        historical_df = fetch_live_crypto_data(symbol=symbol, limit=500)
        if historical_df is not None:
            bootstrap_processed = detector.prepare_features(historical_df)
            detector.train(bootstrap_processed)
        
    processed_df = detector.prepare_features(df)
    detector.train(processed_df) # This will now use self-supervised learning on live data
    probs = detector.predict(processed_df)
    processed_df['fraud_prob'] = probs
    processed_df['is_detected'] = (processed_df['fraud_prob'] > threshold).astype(int)
    
    # Generate Trading Signals
    # Load optimized parameters if available
    config_path = "models/trading_config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            best_params = json.load(f)
        strategy = TradingStrategy(**best_params)
    else:
        strategy = TradingStrategy()
        
    processed_df['signal'] = strategy.generate_signals(processed_df)
    
    # Advanced Deep Learning Analysis
    if use_deep_learning:
        with st.spinner("Running LSTM Sequence Analysis..."):
            deep_detector = DeepFraudDetector(input_dim=8)
            features = ['price', 'volume', 'price_change', 'vol_change', 'volatility', 'dist_from_sma', 'rsi', 'bb_width']
            deep_detector.train_model(processed_df, features, epochs=10)
            deep_scores = deep_detector.get_anomaly_scores(processed_df, features)
            # Normalize deep scores and combine with existing prob
            deep_scores_norm = (deep_scores - deep_scores.min()) / (deep_scores.max() - deep_scores.min() + 1e-6)
            processed_df['fraud_prob'] = (processed_df['fraud_prob'] * 0.6) + (deep_scores_norm * 0.4)
            processed_df['is_detected'] = (processed_df['fraud_prob'] > threshold).astype(int)
            # Update signals based on deep risk
            processed_df['signal'] = strategy.generate_signals(processed_df)

    # Handle Notifications for new detections
    if enable_logging:
        notifier = Notifier(webhook_url=webhook_url)
        frauds = processed_df[processed_df['is_detected'] == 1]
        for _, row in frauds.iterrows():
            notifier.log_alert(row['symbol'], row['price'], row['fraud_prob'], row['timestamp'])
            
    return processed_df

with st.spinner("Analyzing market patterns..."):
    if mode == "Synthetic":
        df = get_data(mode, data_points)
    else:
        df = get_data(mode, data_points, symbol=symbol)

# Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Price", f"${df['price'].iloc[-1]:,.2f}", f"{df['price'].pct_change().iloc[-1]*100:.2f}%")
col2.metric("Total Transactions", len(df))
col3.metric("Detected Frauds", df['is_detected'].sum())
col4.metric("Avg Risk Score", f"{df['fraud_prob'].mean()*100:.1f}%")

# Main Chart
st.subheader("Market Activity & Anomaly Detection")
fig = go.Figure()

# Bollinger Bands
fig.add_trace(go.Scatter(
    x=df['timestamp'], y=df['bb_upper'],
    name='BB Upper',
    line=dict(color='rgba(255, 255, 255, 0.2)', width=1, dash='dot')
))
fig.add_trace(go.Scatter(
    x=df['timestamp'], y=df['bb_lower'],
    name='BB Lower',
    line=dict(color='rgba(255, 255, 255, 0.2)', width=1, dash='dot'),
    fill='tonexty', fillcolor='rgba(255, 255, 255, 0.05)'
))

# Price Line
fig.add_trace(go.Scatter(
    x=df['timestamp'], y=df['price'],
    name='Price',
    line=dict(color='#00d1b2', width=2)
))

# Highlight Detected Frauds
fraud_df = df[df['is_detected'] == 1]
fig.add_trace(go.Scatter(
    x=fraud_df['timestamp'], y=fraud_df['price'],
    name='Detected Fraud',
    mode='markers',
    marker=dict(color='#ff4b4b', size=10, symbol='x')
))

# Add Trading Signals
buy_signals = df[df['signal'] == "BUY"]
fig.add_trace(go.Scatter(
    x=buy_signals['timestamp'], y=buy_signals['price'],
    name='BUY Signal',
    mode='markers',
    marker=dict(color='#00ff00', size=12, symbol='triangle-up', line=dict(width=1, color='white'))
))

sell_signals = df[df['signal'] == "SELL"]
fig.add_trace(go.Scatter(
    x=sell_signals['timestamp'], y=sell_signals['price'],
    name='SELL Signal',
    mode='markers',
    marker=dict(color='#ff00ff', size=12, symbol='triangle-down', line=dict(width=1, color='white'))
))

fig.update_layout(
    template="plotly_dark",
    height=500,
    margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# RSI Chart
st.subheader("RSI (Relative Strength Index)")
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(
    x=df['timestamp'], y=df['rsi'],
    name='RSI',
    line=dict(color='#ffa500', width=1.5)
))
# Overbought/Oversold levels
fig_rsi.add_hline(y=70, line_dash="dash", line_color="rgba(255, 75, 75, 0.5)")
fig_rsi.add_hline(y=30, line_dash="dash", line_color="rgba(0, 209, 178, 0.5)")

fig_rsi.update_layout(
    template="plotly_dark",
    height=250,
    margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', range=[0, 100])
)
st.plotly_chart(fig_rsi, use_container_width=True)

# Fraud Feed
st.subheader("Recent Alerts Feed")
if df['is_detected'].sum() > 0:
    recent_frauds = df[df['is_detected'] == 1].sort_values('timestamp', ascending=False).head(5)
    for _, row in recent_frauds.iterrows():
        st.markdown(f"""
        <div class="fraud-alert">
            ⚠️ Alert: Suspicious Activity Detected at {row['timestamp'].strftime('%H:%M:%S')} 
            | Price: ${row['price']:.2f} | Risk Score: {row['fraud_prob']*100:.1f}%
        </div>
        """, unsafe_allow_html=True)
        st.write("")
else:
    st.success("No fraudulent activity detected in the current window.")

# Detailed Data Table
with st.expander("View Raw Analysis Data"):
    st.dataframe(df.sort_values('timestamp', ascending=False), use_container_width=True)

# Footer
st.markdown("---")
st.caption("Powered by Hybrid ML Models (Isolation Forest + XGBoost) | Antigravity AI")
