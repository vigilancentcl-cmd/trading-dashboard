import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Trading Dashboard", layout="wide")
st.title("📈 Auto Trading Dashboard")

# Sidebar Controls
st.sidebar.header("⚙️ Market Settings")
market_type = st.sidebar.selectbox("Market Type", ["Indian Market (NSE)", "US / Global Market"])

if market_type == "Indian Market (NSE)":
    symbol = st.sidebar.text_input("Enter Ticker (e.g. RELIANCE.NS, SBIN.NS, TATAMOTORS.NS)", "RELIANCE.NS")
    tv_symbol = f"NSE:{symbol.replace('.NS', '')}"
else:
    symbol = st.sidebar.text_input("Enter Ticker (e.g. AAPL, TSLA, BTCUSD)", "AAPL")
    tv_symbol = symbol

# -------------------------------------------------------------
# 1. LIVE TRADINGVIEW CHART
# -------------------------------------------------------------
st.subheader("📊 Live Technical Chart")
tradingview_html = f"""
<div class="tradingview-widget-container">
  <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol={tv_symbol}&interval=5&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=RSI%40tv-basicstudies%2CMACD%40tv-basicstudies&theme=dark&style=1&timezone=Asia%2FKolkata" 
          width="100%" height="520" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
</div>
"""
components.html(tradingview_html, height=530)

# -------------------------------------------------------------
# 2. AUTO BUY / SELL / WAIT SIGNAL GENERATOR
# -------------------------------------------------------------
st.subheader("⚡ Automated Entry / Exit Signal")

@st.cache_data(ttl=60)
def get_signal_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="15m", progress=False)
        if df.empty or len(df) < 21:
            return None
        
        # Multi-index fix
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Pure Pandas Calculations
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        return df
    except Exception:
        return None

data = get_signal_data(symbol)

if data is not None and not data.empty:
    latest_rsi = float(data['RSI'].dropna().iloc[-1])
    latest_ema9 = float(data['EMA_9'].dropna().iloc[-1])
    latest_ema21 = float(data['EMA_21'].dropna().iloc[-1])
    last_price = float(data['Close'].dropna().iloc[-1])

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"₹{last_price:.2f}" if ".NS" in symbol else f"${last_price:.2f}")
    col2.metric("RSI (14)", f"{latest_rsi:.2f}")
    col3.metric("EMA Trend", "Bullish" if latest_ema9 > latest_ema21 else "Bearish")

    # Signal Logic
    if latest_ema9 > latest_ema21 and latest_rsi < 70:
        st.success("🟢 **BUY CALL SIGNAL (CE):** Strong Bullish Crossover! Trend Upar hai.")
    elif latest_ema9 < latest_ema21 and latest_rsi > 30:
        st.error("🔴 **BUY PUT SIGNAL (PE):** Strong Bearish Crossover! Trend Niche hai.")
    else:
        st.warning("⏳ **WAIT SIGNAL:** Market Sideways hai. Waiting for clear setup.")
else:
    st.info("⚠️ Enter a valid ticker like RELIANCE.NS, SBIN.NS, or AAPL.")
