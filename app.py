import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="AI Trading Dashboard", layout="wide")
st.title("📈 Auto Trading & News Dashboard")

# Sidebar Controls
st.sidebar.header("⚙️ Market Settings")
market_type = st.sidebar.selectbox("Market Type", ["Indian Market (NSE)", "US / Global Market"])

if market_type == "Indian Market (NSE)":
    symbol = st.sidebar.text_input("Enter Ticker (e.g. ^NSEI for Nifty, RELIANCE.NS)", "^NSEI")
    if symbol == "^NSEI":
        tv_symbol = "NSE:NIFTY"
    else:
        tv_symbol = f"NSE:{symbol.replace('.NS', '')}"
else:
    symbol = st.sidebar.text_input("Enter Ticker (e.g. AAPL, TSLA, BTC-USD)", "AAPL")
    tv_symbol = symbol

# -------------------------------------------------------------
# 1. LIVE TRADINGVIEW CHART WITH INDICATORS
# -------------------------------------------------------------
st.subheader("📊 Live Technical Chart")
tradingview_html = f"""
<div class="tradingview-widget-container">
  <div id="tradingview_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "width": "100%",
    "height": 500,
    "symbol": "{tv_symbol}",
    "interval": "5",
    "timezone": "Asia/Kolkata",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "MASimple@tv-basicstudies"],
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tradingview_html, height=520)

# -------------------------------------------------------------
# 2. AUTO BUY / SELL / WAIT SIGNAL GENERATOR
# -------------------------------------------------------------
st.subheader("⚡ Automated Entry / Exit Signal")

@st.cache_data(ttl=60)
def get_signal_data(ticker):
    df = yf.download(ticker, period="5d", interval="15m")
    if df.empty:
        return None, None
    
    # Calculate RSI & Moving Averages
    df['RSI'] = ta.momentum.rsi(df['Close'].squeeze(), window=14)
    df['EMA_9'] = ta.trend.ema_indicator(df['Close'].squeeze(), window=9)
    df['EMA_21'] = ta.trend.ema_indicator(df['Close'].squeeze(), window=21)
    return df

data = get_signal_data(symbol)

if data is not None and not data.empty:
    latest_rsi = data['RSI'].iloc[-1]
    latest_ema9 = data['EMA_9'].iloc[-1]
    latest_ema21 = data['EMA_21'].iloc[-1]
    last_price = data['Close'].iloc[-1].item()

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"{last_price:.2f}")
    col2.metric("RSI (14)", f"{latest_rsi:.2f}")
    col3.metric("EMA Trend", "Bullish" if latest_ema9 > latest_ema21 else "Bearish")

    # Signal Logic
    if latest_ema9 > latest_ema21 and latest_rsi < 70:
        st.success("🟢 **BUY CALL SIGNAL (CE):** Strong Bullish Crossover! Trend Upar hai. Entry le sakte hain.")
    elif latest_ema9 < latest_ema21 and latest_rsi > 30:
        st.error("🔴 **BUY PUT SIGNAL (PE):** Strong Bearish Crossover! Trend Niche hai. Entry le sakte hain.")
    else:
        st.warning("⏳ **WAIT SIGNAL:** Market Sideways / Volatile hai. Abhi koi clear setup nahi hai, wait karein.")
else:
    st.info("No data fetched for signals.")

# -------------------------------------------------------------
# 3. GLOBAL & INDIAN MARKET NEWS
# -------------------------------------------------------------
st.subheader("📰 Market News (Indian & Global)")

tab1, tab2 = st.tabs(["🇮🇳 Indian Market News", "🌐 Global Market News"])

def fetch_news(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&apiKey=YOUR_NEWS_API_KEY"
    try:
        # Simple RSS alternative for quick display
        feed_url = f"https://news.google.com/rss/search?q={topic}&hl=en-IN&gl=IN&ceid=IN:en"
        import xml.etree.ElementTree as ET
        res = requests.get(feed_url)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5]
        return items
    except:
        return []

with tab1:
    news_items = fetch_news("Indian Stock Market Nifty Sensex")
    for item in news_items:
        title = item.find('title').text if item.find('title') is not None else ""
        link = item.find('link').text if item.find('link') is not None else "#"
        st.write(f"- [{title}]({link})")

with tab2:
    news_items_global = fetch_news("Global Market Fed Inflation Stocks")
    for item in news_items_global:
        title = item.find('title').text if item.find('title') is not None else ""
        link = item.find('link').text if item.find('link') is not None else "#"
        st.write(f"- [{title}]({link})")
