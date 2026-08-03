import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Pro Trading Dashboard", layout="wide")
st.title("⚡ Pro Trading Dashboard")

# Sidebar Setup
st.sidebar.header("Market Settings")
user_input = st.sidebar.text_input("Enter Ticker (e.g. RELIANCE, SBIN, ^NSEI, AAPL)", "RELIANCE")

clean_input = user_input.strip().upper()

# Symbol Formatting
if clean_input.startswith("^") or clean_input in ["AAPL", "TSLA", "MSFT", "NVDA", "BTC-USD"]:
    yf_symbol = clean_input
else:
    yf_symbol = clean_input.replace(".NS", "") + ".NS"

# Fetch Data
@st.cache_data(ttl=60)
def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="15m")
        return df if not df.empty else None
    except Exception:
        return None

df = fetch_stock_data(yf_symbol)

if df is not None and not df.empty and len(df) >= 14:
    close = df['Close']
    last_price = float(close.iloc[-1])
    
    # Technical Indicators
    ema_9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema_21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    # 1. LIVE PRICE CHART (ST.LINE_CHART)
    st.subheader(f"📊 Price Movement Chart: {clean_input}")
    chart_df = df[['Close', 'Open', 'High', 'Low']]
    st.line_chart(chart_df['Close'], height=400)

    # 2. METRICS & SIGNALS
    st.subheader("⚡ Signal Engine")
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"₹{last_price:.2f}" if not clean_input.startswith("AAPL") else f"${last_price:.2f}")
    c2.metric("RSI (14)", f"{rsi:.2f}")
    c3.metric("Trend", "Bullish 🟢" if ema_9 > ema_21 else "Bearish 🔴")

    if ema_9 > ema_21 and rsi < 70:
        st.success("🟢 **BUY CE SIGNAL:** Strong Bullish Trend")
    elif ema_9 < ema_21 and rsi > 30:
        st.error("🔴 **BUY PE SIGNAL:** Strong Bearish Trend")
    else:
        st.warning("⏳ **WAIT:** Sideways Market")

    # 3. RECENT DATA TABLE
    with st.expander("🔍 View Recent Price Data"):
        st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10))

else:
    st.error("⚠️ Stock data load nahi ho pa raha. Valid symbol enter karein (e.g. RELIANCE, SBIN, ^NSEI).")
