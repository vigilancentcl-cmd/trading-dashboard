import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📈 Auto Trading Dashboard")

# Sidebar Setup
st.sidebar.header("Market Settings")
market_type = st.sidebar.selectbox("Market Type", ["Indian Market (NSE)", "US / Global Market"])

if market_type == "Indian Market (NSE)":
    user_input = st.sidebar.text_input("Enter NSE Ticker (e.g. RELIANCE, SBIN, TATAMOTORS)", "RELIANCE")
    clean_symbol = user_input.strip().upper().replace(".NS", "")
    yf_ticker = f"{clean_symbol}.NS"
    tv_ticker = f"NSE:{clean_symbol}"
else:
    user_input = st.sidebar.text_input("Enter Ticker (e.g. AAPL, TSLA, BTCUSD)", "AAPL")
    clean_symbol = user_input.strip().upper()
    yf_ticker = clean_symbol
    tv_ticker = clean_symbol

# 1. TRADINGVIEW LIVE CHART WIDGET
st.subheader(f"📊 Live Technical Chart ({clean_symbol})")
chart_html = f"""
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol={tv_ticker}&interval=5&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=RSI%40tv-basicstudies&theme=dark&style=1&timezone=Asia%2FKolkata" 
        width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
"""
st.components.v1.html(chart_html, height=520)

# 2. AUTO BUY / SELL / WAIT SIGNALS
st.subheader("⚡ Automated Entry / Exit Signal")

@st.cache_data(ttl=60)
def fetch_stock_data(symbol):
    try:
        data = yf.Ticker(symbol)
        df = data.history(period="5d", interval="15m")
        return df
    except Exception:
        return None

df = fetch_stock_data(yf_ticker)

if df is not None and not df.empty and len(df) >= 21:
    close = df['Close']
    
    # Pure Pandas Calculations
    ema_9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema_21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    last_price = float(close.iloc[-1])

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"₹{last_price:.2f}" if market_type == "Indian Market (NSE)" else f"${last_price:.2f}")
    col2.metric("RSI (14)", f"{rsi:.2f}")
    col3.metric("EMA Trend", "Bullish" if ema_9 > ema_21 else "Bearish")

    if ema_9 > ema_21 and rsi < 70:
        st.success("🟢 **BUY CALL SIGNAL (CE):** Bullish Crossover! Trend Upar Hai.")
    elif ema_9 < ema_21 and rsi > 30:
        st.error("🔴 **BUY PUT SIGNAL (PE):** Bearish Crossover! Trend Niche Hai.")
    else:
        st.warning("⏳ **WAIT SIGNAL:** Market Sideways Hai. Wait For Clear Setup.")
else:
    st.info("⚠️ Data fetch ho raha hai ya Ticker invalid hai. Sahi symbol daalein (e.g. RELIANCE, SBIN).")
