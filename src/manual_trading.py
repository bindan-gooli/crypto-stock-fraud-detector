import streamlit as st
import time
from src.live_ingestion import fetch_live_crypto_data
import plotly.graph_objects as go

st.set_page_config(page_title="Manual Trading Tracker", page_icon="📈", layout="centered")

st.title("📈 Manual Trading Tracker")
st.markdown("Follow the buy/sell targets and manually record your entries.")

# Initialize Session State for holding position
if 'position' not in st.session_state:
    st.session_state.position = None
if 'buy_price' not in st.session_state:
    st.session_state.buy_price = 0.0
if 'sell_target' not in st.session_state:
    st.session_state.sell_target = 0.0
if 'symbol' not in st.session_state:
    st.session_state.symbol = "BTCUSDT"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "LINKUSDT"]

if st.session_state.position is None:
    # Scanning Mode
    st.subheader("🔍 Scan for Opportunities")
    selected_symbol = st.selectbox("Select Asset to Track", SYMBOLS, index=SYMBOLS.index(st.session_state.symbol))
    st.session_state.symbol = selected_symbol
    
    window_size = 15
    df = fetch_live_crypto_data(symbol=selected_symbol, interval="1m", limit=50)
    
    if df is not None and len(df) >= window_size:
        # Use last 15 candles for targets
        target_df = df.iloc[-window_size:]
        prices = sorted(target_df['price'].tolist())
        current_price = df.iloc[-1]['price']
        buy_target = prices[1]  # 2nd lowest
        sell_target = prices[-2]  # 2nd highest
        
        st.metric("Current Price", f"${current_price:.6f}")
        
        col1, col2 = st.columns(2)
        col1.metric("Buy Target (2nd Lowest)", f"${buy_target:.6f}")
        col2.metric("Sell Target (2nd Highest)", f"${sell_target:.6f}")
        
        # Draw Live Chart
        st.subheader("📊 Live Market Chart")
        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'], high=df['high'],
            low=df['low'], close=df['price'],
            name='Price'
        )])
        fig.add_hline(y=buy_target, line_dash="dash", line_color="green", annotation_text="Buy Target")
        fig.add_hline(y=sell_target, line_dash="dash", line_color="red", annotation_text="Sell Target")
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        if current_price <= buy_target:
            st.success(f"🟢 **BUY POINT REACHED!** Consider buying {selected_symbol} around ${current_price:.6f}")
        else:
            st.info(f"⏳ Waiting for price to drop to Buy Target (${buy_target:.6f})...")
            
        st.subheader("📝 Record Manual Entry")
        with st.form("buy_form"):
            user_buy_price = st.number_input("Enter your actual Buy Price:", value=float(current_price), format="%.6f")
            submitted = st.form_submit_button("Note Buy Point")
            
            if submitted:
                st.session_state.position = "HOLD"
                st.session_state.buy_price = user_buy_price
                st.session_state.sell_target = sell_target
                st.rerun()
    else:
        st.warning("Not enough data to calculate targets.")
        
else:
    # Holding Mode
    st.subheader(f"🛡️ Holding {st.session_state.symbol}")
    
    df = fetch_live_crypto_data(symbol=st.session_state.symbol, interval="1m", limit=50)
    if df is not None:
        current_price = df.iloc[-1]['price']
        profit_loss = current_price - st.session_state.buy_price
        pl_pct = (profit_loss / st.session_state.buy_price) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Your Buy Price", f"${st.session_state.buy_price:.6f}")
        col2.metric("Current Price", f"${current_price:.6f}", f"{pl_pct:.2f}%")
        col3.metric("Target Sell Price", f"${st.session_state.sell_target:.6f}")
        
        # Draw Live Chart
        st.subheader("📊 Live Market Chart")
        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'], high=df['high'],
            low=df['low'], close=df['price'],
            name='Price'
        )])
        fig.add_hline(y=st.session_state.buy_price, line_dash="solid", line_color="blue", annotation_text="Your Buy Price")
        fig.add_hline(y=st.session_state.sell_target, line_dash="dash", line_color="red", annotation_text="Sell Target")
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        
        if current_price >= st.session_state.sell_target:
            st.error(f"🔴 **SELL POINT REACHED!** Sell {st.session_state.symbol} NOW!")
            st.toast("SELL POINT REACHED!", icon="🚨")
        else:
            st.warning("HOLD: Waiting for Sell Target to be reached...")
            
        if st.button("Mark as Sold"):
            st.session_state.position = None
            st.session_state.buy_price = 0.0
            st.session_state.sell_target = 0.0
            st.success("Trade closed successfully!")
            st.rerun()

    if st.button("Refresh Price"):
        st.rerun()
