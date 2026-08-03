import streamlit as st
import yfinance as yf
import json

st.set_page_config(page_title="Pro Trading Dashboard", layout="wide")
st.title("⚡ Pro Canvas Trading Dashboard")

# Sidebar
st.sidebar.header("Market Settings")
ticker_input = st.sidebar.text_input("Enter NSE Ticker (e.g. RELIANCE, SBIN, TATAMOTORS)", "RELIANCE")

clean_ticker = ticker_input.strip().upper().replace(".NS", "")
yf_symbol = f"{clean_ticker}.NS"

# Data Fetching
@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if hasattr(data.columns, 'levels'):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception:
        return None

df = get_data(yf_symbol)

if df is not None and not df.empty:
    # 1. LIGHTWEIGHT CANVAS CANDLESTICK CHART (NEW METHOD)
    chart_data = []
    for index, row in df.iterrows():
        chart_data.append({
            "time": int(index.timestamp()),
            "open": float(row['Open']),
            "high": float(row['High']),
            "low": float(row['Low']),
            "close": float(row['Close'])
        })

    json_data = json.dumps(chart_data)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            #chart {{ width: 100%; height: 450px; background-color: #111; }}
        </style>
    </head>
    <body style="margin:0; background-color: #111;">
        <div id="chart"></div>
        <script>
            const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
                layout: {{ backgroundColor: '#111111', textColor: '#d1d4dc' }},
                grid: {{ vertLines: {{ color: '#222' }}, horzLines: {{ color: '#222' }} }},
                timeScale: {{ timeVisible: true, secondsVisible: false }}
            }});
            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
                wickUpColor: '#26a69a', wickDownColor: '#ef5350'
            }});
            candlestickSeries.setData({json_data});
            chart.timeScale().fitContent();
        </script>
    </body>
    </html>
    """

    st.subheader(f"📊 Pure HTML5 Chart: {clean_ticker}")
    st.components.v1.html(html_code, height=470)

    # 2. SIGNALS
    st.subheader("⚡ Signal Engine")
    close = df['Close']
    last_price = float(close.iloc[-1])
    
    ema_9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema_21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"₹{last_price:.2f}")
    c2.metric("RSI (14)", f"{rsi:.2f}")
    c3.metric("Trend", "Bullish 🟢" if ema_9 > ema_21 else "Bearish 🔴")

    if ema_9 > ema_21 and rsi < 70:
        st.success("🟢 **BUY CE SIGNAL:** Strong Bullish Crossover")
    elif ema_9 < ema_21 and rsi > 30:
        st.error("🔴 **BUY PE SIGNAL:** Strong Bearish Crossover")
    else:
        st.warning("⏳ **WAIT:** Sideways Market")

else:
    st.error("⚠️ Stock data load nahi ho pa raha. Ticker name check karein.")
