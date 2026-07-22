import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from openai import OpenAI

# ---------------------------------------------------------
# 1. PAGE SETUP & AUTO-REFRESH (EST Timezone)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Macro Fundamental Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh app every 60 seconds
st_autorefresh(interval=60000, limit=None, key="macro_auto_refresh")

st.markdown("""
    <style>
        .stApp { background-color: #0B0E14; color: #E2E8F0; }
        div[data-testid="stMetric"] { background-color: #161B22; border: 1px solid #30363D; padding: 12px; border-radius: 8px; }
        .bias-card { background-color: #161B22; padding: 18px; border-radius: 8px; margin-bottom: 14px; border-left: 5px solid #30363D; }
        .bullish { border-left-color: #10B981 !important; }
        .bearish { border-left-color: #EF4444 !important; }
        .neutral { border-left-color: #F59E0B !important; }
        .badge-bull { color: #10B981; font-weight: bold; }
        .badge-bear { color: #EF4444; font-weight: bold; }
        .badge-neu  { color: #F59E0B; font-weight: bold; }
        h1, h2, h3 { color: #F8FAFC !important; }
    </style>
""", unsafe_allow_html=True)

# Enforce Eastern Time Zone (EST / NY Time)
est_tz = pytz.timezone('America/New_York')
now_est = datetime.datetime.now(est_tz).strftime("%I:%M:%S %p EST")

# ---------------------------------------------------------
# 2. LIVE MARKET & WEB DATA SCRAPERS
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def get_live_prices():
    """Fetches real-time prices for DXY, XAUUSD, NQ, and US30"""
    tickers = {
        "DXY": "DX-Y.NYB",
        "XAUUSD": "GC=F",
        "NQ": "NQ=F",
        "US30": "YM=F"
    }
    data = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            fast = t.fast_info
            price = fast['lastPrice']
            prev = fast['previousClose']
            chg = ((price - prev) / prev) * 100
            data[name] = {"price": price, "change": chg}
        except Exception:
            data[name] = {"price": 0.0, "change": 0.0}
    return data

@st.cache_data(ttl=120)
def fetch_web_news():
    """Pulls breaking economic headlines from Google News RSS"""
    try:
        url = "https://news.google.com/rss/search?q=forex+economy+fed+inflation+when:1d&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")[:6]
        return [item.title.text for item in items]
    except Exception:
        return [
            "Federal Reserve signals caution on upcoming interest rate decisions.",
            "US Dollar Index consolidates amidst shifting yield environment.",
            "Equity markets digest recent producer price and consumer sentiment data."
        ]

# ---------------------------------------------------------
# 3. AI MACRO SYNTHESIS ENGINE (XAUUSD, NQ, US30 ONLY)
# ---------------------------------------------------------
def analyze_macro_with_ai(news_list, prices):
    """Sends live economic news & market metrics to GPT-4o to output fundamental biases"""
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    if not api_key:
        return {
            "regime": "API KEY MISSING",
            "biases": {
                "XAUUSD": {"bias": "NEUTRAL", "type": "neutral", "driver": "Please add OPENAI_API_KEY in Streamlit Secrets to enable live AI web analysis."},
                "NQ": {"bias": "NEUTRAL", "type": "neutral", "driver": "Please add OPENAI_API_KEY in Streamlit Secrets to enable live AI web analysis."},
                "US30": {"bias": "NEUTRAL", "type": "neutral", "driver": "Please add OPENAI_API_KEY in Streamlit Secrets to enable live AI web analysis."}
            }
        }
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    You are an institutional macro trader analyzing fundamental biases for Gold (XAUUSD), Nasdaq 100 (NQ), and Dow Jones (US30).
    
    Current Web Headlines: {news_list}
    Current Asset Prices & % Changes: {prices}
    
    Synthesize these data points into institutional biases based on US Dollar flows, interest rate outlook, and broader risk sentiment.
    
    Output JSON ONLY in this exact format:
    {{
        "regime": "RISK-ON or RISK-OFF",
        "biases": {{
            "XAUUSD": {{"bias": "BULLISH/BEARISH/NEUTRAL", "driver": "1 concise sentence explaining the fundamental driver (e.g. Fed policy, DXY, real yields, safe haven flow)"}},
            "NQ": {{"bias": "BULLISH/BEARISH/NEUTRAL", "driver": "1 concise sentence explaining the fundamental driver (e.g. yield impact on growth tech, rate expectations)"}},
            "US30": {{"bias": "BULLISH/BEARISH/NEUTRAL", "driver": "1 concise sentence explaining the fundamental driver (e.g. industrial earnings, cyclical rotation, economic strength)"}}
        }}
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        res_json = json.loads(response.choices[0].message.content)
        
        for k, v in res_json["biases"].items():
            v["type"] = v["bias"].lower()
            
        return res_json
    except Exception as e:
        return {
            "regime": "ANALYSIS ERROR",
            "biases": {
                "XAUUSD": {"bias": "NEUTRAL", "type": "neutral", "driver": f"Error running AI analysis: {str(e)}"},
                "NQ": {"bias": "NEUTRAL", "type": "neutral", "driver": "Error running AI analysis."},
                "US30": {"bias": "NEUTRAL", "type": "neutral", "driver": "Error running AI analysis."}
            }
        }

# ---------------------------------------------------------
# 4. RENDER DASHBOARD
# ---------------------------------------------------------
prices = get_live_prices()
news = fetch_web_news()
ai_analysis = analyze_macro_with_ai(news, prices)

st.title("⚡ AI MACRO & FUNDAMENTAL DASHBOARD")
st.caption(f"🤖 Automated Web Analysis | All Times in **New York Time (EST)** | Last Update: **{now_est}**")

st.markdown("---")

# Metrics Bar (EST Focus)
st.markdown("### 🌐 Live Market Overview")
m1, m2, m3, m4 = st.columns(4)

dxy = prices.get("DXY", {"price": 0, "change": 0})
gold = prices.get("XAUUSD", {"price": 0, "change": 0})
nq = prices.get("NQ", {"price": 0, "change": 0})
us30 = prices.get("US30", {"price": 0, "change": 0})

with m1:
    st.metric(label="US Dollar Index (DXY)", value=f"{dxy['price']:.2f}", delta=f"{dxy['change']:+.2f}%")
with m2:
    st.metric(label="Macro Regime", value=ai_analysis.get("regime", "RISK-ON"))
with m3:
    st.metric(label="Gold (XAUUSD)", value=f"${gold['price']:,.2f}", delta=f"{gold['change']:+.2f}%")
with m4:
    st.metric(label="Nasdaq 100 (NQ)", value=f"${nq['price']:,.2f}", delta=f"{nq['change']:+.2f}%")

st.markdown("---")

# Asset Biases (3 Focus Assets: Gold, NQ, US30)
st.markdown("### 🎯 Live Fundamental Biases")
c1, c2, c3 = st.columns(3)

biases = ai_analysis.get("biases", {})

asset_cols = [
    ("XAUUSD", "XAUUSD (Gold)", c1),
    ("NQ", "NQ (Nasdaq 100)", c2),
    ("US30", "US30 (Dow Jones)", c3)
]

for sym, label, col in asset_cols:
    with col:
        item = biases.get(sym, {"bias": "NEUTRAL", "type": "neutral", "driver": "Analyzing market conditions..."})
        p = prices.get(sym, {"price": 0})["price"]
        st.markdown(f"""
        <div class="bias-card {item['type']}">
            <h3 style="margin:0; font-size:1.15rem;">{label} — <span class="badge-{item['type'][:4]}">{item['bias']}</span></h3>
            <p style="margin: 8px 0; color: #CBD5E1; font-size: 0.95rem;"><b>Macro Driver:</b> {item['driver']}</p>
            <p style="margin:0; color: #64748B; font-size: 0.85rem;"><b>Live Price:</b> ${p:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Breaking Wire
st.markdown("### 📡 Breaking Economic News Wire (Web Search)")
for n in news:
    st.info(f"📰 {n}")
