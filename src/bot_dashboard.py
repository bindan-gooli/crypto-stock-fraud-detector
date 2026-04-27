import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from src.live_ingestion import fetch_live_crypto_data
from src.model import FraudDetector

# Page Config
st.set_page_config(
    page_title="Crypto Guard | Live Bot Monitor",
    page_icon="🤖",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-container {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    .status-live {
        color: #00ff00;
        font-weight: bold;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Live Trading Bot Monitor")
st.markdown("---")

# Sidebar for controls
st.sidebar.title("Bot Controls")
st.sidebar.markdown(f"**Session Start**: {datetime.now().strftime('%Y-%m-%d')}")
st.sidebar.markdown("---")
if st.sidebar.button("Force Refresh Data"):
    st.rerun()

# Load Data
results_dir = "ultra_scalp_results" if os.path.exists("ultra_scalp_results") else ("scalper_results" if os.path.exists("scalper_results") else "live_trading_results")
status_file = f"{results_dir}/status.json"
history_file = f"{results_dir}/trade_history.csv"

if os.path.exists(status_file):
    with open(status_file, "r") as f:
        status = json.load(f)
    
    # Metrics Header
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Wallet Value", f"${status['total_value']:,.2f}", f"{((status['total_value']-1000)/1000)*100:.4f}%")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.write("**Active Asset(s)**")
        active = status.get('active_positions', status.get('active_asset', 'None'))
        if isinstance(active, list):
            st.subheader(", ".join(active) if active else "None")
        else:
            st.subheader(active)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.write("**Cash Balance**")
        st.subheader(f"${status['balance']:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        trades_done = status.get('trades_done', 0)
        st.metric("Total Trades", trades_done)
        st.markdown('</div>', unsafe_allow_html=True)

    # Market Chart
    st.markdown("---")
    active_list = status.get('active_positions', [status.get('active_asset', 'BTCUSDT')])
    if isinstance(active_list, str): active_list = [active_list]
    asset_to_show = active_list[0] if active_list and active_list[0] != "None (Scanning...)" else "BTCUSDT"
    st.subheader(f"Live Market: {asset_to_show}")
    
    with st.spinner(f"Fetching live candles for {asset_to_show}..."):
        df_live = fetch_live_crypto_data(symbol=asset_to_show, interval="1m", limit=50)
        if df_live is not None:
            detector = FraudDetector()
            df_live = detector.prepare_features(df_live)
            
            # Create Candlestick Chart with Indicators
            fig_market = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                      vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Candles
            fig_market.add_trace(go.Candlestick(
                x=df_live['timestamp'],
                open=df_live['open'], high=df_live['high'],
                low=df_live['low'], close=df_live['price'],
                name='Price'
            ), row=1, col=1)
            
            # Bollinger Bands
            fig_market.add_trace(go.Scatter(x=df_live['timestamp'], y=df_live['bb_upper'], name='BB Upper', line=dict(color='rgba(255,255,255,0.2)'), fill=None), row=1, col=1)
            fig_market.add_trace(go.Scatter(x=df_live['timestamp'], y=df_live['bb_lower'], name='BB Lower', line=dict(color='rgba(255,255,255,0.2)'), fill='tonexty'), row=1, col=1)
            
            # RSI
            fig_market.add_trace(go.Scatter(x=df_live['timestamp'], y=df_live['rsi'], name='RSI', line=dict(color='#ff9900')), row=2, col=1)
            fig_market.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig_market.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig_market.update_layout(
                template="plotly_dark",
                height=600,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_rangeslider_visible=False,
                showlegend=False
            )
            st.plotly_chart(fig_market, use_container_width=True)

    # Trade History Table & Performance Chart
    st.markdown("---")
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Performance Over Time")
        if os.path.exists(history_file):
            df_history = pd.read_csv(history_file)
            if not df_history.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_history['timestamp'], 
                    y=df_history['total_value'],
                    mode='lines+markers',
                    line=dict(color='#00ff00', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 0, 0.1)'
                ))
                fig.update_layout(
                    template="plotly_dark",
                    height=400,
                    margin=dict(l=20, r=20, t=20, b=20),
                    yaxis_title="Wallet Value ($)",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Waiting for first trade to generate performance chart...")
        
    with col_right:
        st.subheader("Recent Execution Log")
        if os.path.exists(history_file):
            df_history = pd.read_csv(history_file)
            if not df_history.empty:
                st.dataframe(
                    df_history.sort_values('timestamp', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.write("No trades executed yet. Bot is scanning markets...")

    # Current Position Details
    if 'active_positions' in status or (status.get('active_asset') and status['active_asset'] != "None (Scanning...)"):
        st.markdown("---")
        st.subheader("Position Overview")
        if 'active_positions' in status:
            st.write(f"Currently tracking {len(status['active_positions'])} open trades.")
        else:
            st.write(f"Holding: {status['active_asset']}")
else:
    st.warning("Waiting for the Live Trading Bot to initialize status files...")
    st.info("Ensure the bot script is running in the background.")

# Footer
st.markdown("---")
st.caption("Live Bot Monitor v1.0 | Powered by Antigravity AI | Scanning: BTC, ETH, SOL, BNB, ADA")
