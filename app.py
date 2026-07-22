import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. PAGE SETUP & AUTO-REFRESH
# ---------------------------------------------------------
st.set_page_config(
    page_title="HybridTrader — AI Macro Desk",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh silently every 60 seconds
st_autorefresh(interval=60000, limit=None, key="macro_auto_refresh")

# Enforce Eastern Time Zone (EST / NY Time)
est_tz = pytz.timezone('America/New_York')
now_est = datetime.datetime.now(est_tz).strftime("%H:%M:%S EST")

# Precise CSS Styling matching HybridTrader UI
st.html("""
<style>
    /* Dark Theme Base */
    .stApp { background-color: #0B0E13; color: #E2E8F0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    
    /* Macro Cards */
    .macro-card {
        background-color: #12161F;
        border: 1px solid #1A212D;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    
    /* Badges */
    .badge {
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .badge-bullish { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-bearish { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-neutral { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.4); }
    
    /* Custom Progress Bar for Confidence */
    .confidence-bg {
        width: 100%;
        background-color: #1A2230;
        border-radius: 4px;
        height: 6px;
        margin-top: 6px;
        margin-bottom: 14px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        background: #10B981;
    }
    
    /* Typography */
    .asset-name { font-size: 1.15rem; font-weight: 700; color: #FFFFFF; }
    .price-text { font-size: 0.88rem; font-weight: 600; margin-right: 8px; }
    .up { color: #10B981; }
    .down { color: #EF4444; }
    .ai-label { font-size: 0.8rem; font-weight: 600; color: #38BDF8; margin-bottom: 4px; display: flex; align-items: center; gap: 4px; }
    .ai-desc { font-size: 0.88rem; color: #94A3B8; line-height: 1.45; }
    
    /* Bottom Correlation Grid */
    .corr-card {
        background-color: #12161F;
        border: 1px solid #1A212D;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    
    h1, h2, h3, h4 { color: #F8FAFC !important; }
</style>
""")

# ---------------------------------------------------------
# 2. MARKET DATA & WEB SCRAPERS
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def get_live_prices():
    tickers = {
        "XAUUSD": "GC=F",
        "NQ": "NQ=F",
        "US30": "YM=F",
        "DXY": "DX-Y.NYB",
        "US10Y": "^TNX",
        "VIX": "^VIX",
        "CL": "CL=F"
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
    try:
        url = "https://news.google.com/rss/search?q=forex+economy+fed+inflation+when:1d&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")[:4]
        return [item.title.text for item in items]
    except Exception:
        return [
            "Federal Reserve maintains cautious tone ahead of upcoming inflation and labor data.",
            "US Treasury Yields flatten as market digests recent economic sentiment reports.",
            "Equity markets trade mixed amidst earnings projections and geopolitical watch."
        ]

# ---------------------------------------------------------
# 3. ADVANCED DYNAMIC MACRO & AI ENGINE
# ---------------------------------------------------------
def generate_macro_synthesis(prices, news):
    # Try OpenAI API if user configured key in secrets
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
            Analyze live macro data for Gold (XAUUSD), Nasdaq 100 (NQ), and Dow Jones (US30).
            Prices & Changes: {prices}
            Headlines: {news}
            Return JSON in format:
            {{
                "mood": "RISK-ON or RISK-OFF or RISK-NEUTRAL",
                "mood_summary": "Short 2-sentence institutional summary of capital flows.",
                "biases": {{
                    "XAUUSD": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 75, "driver": "Concise fundamental description."}},
                    "NQ": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 82, "driver": "Concise fundamental description."}},
                    "US30": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 68, "driver": "Concise fundamental description."}}
                }}
            }}
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            import json
            return json.loads(response.choices[0].message.content)
        except Exception:
            pass

    # Built-in Dynamic Fallback Macro Engine (Generates descriptions automatically)
    dxy_chg = prices.get("DXY", {}).get("change", 0)
    us10y_chg = prices.get("US10Y", {}).get("change", 0)
    vix_chg = prices.get("VIX", {}).get("change", 0)
    nq_chg = prices.get("NQ", {}).get("change", 0)
    us30_chg = prices.get("US30", {}).get("change", 0)
    
    # Environment Risk Calculation
    if vix_chg > 3.0 or dxy_chg > 0.4:
        mood = "RISK-OFF"
        mood_summary = "Capital flows are leaning defensive as rising yields and volatility press equity risk premiums. Safe-haven assets attract flows while growth equities face headwinds."
    elif vix_chg < -2.0 and dxy_chg < 0:
        mood = "RISK-ON"
        mood_summary = "Risk sentiment remains upbeat with easing yields and a softer US Dollar driving bullish capital allocation into tech equities and risk assets."
    else:
        mood = "RISK-NEUTRAL"
        mood_summary = "Markets are consolidating in a neutral regime. Traders are digesting macro news and positioning around technical support levels ahead of key policy catalysts."

    # Gold Analysis
    if dxy_chg < 0 or us10y_chg < 0:
        g_bias, g_conf = "BULLISH", 78
        g_driver = "Gold catches a bid as real yields moderate and a softer US Dollar provides underlying support for precious metals."
    else:
        g_bias, g_conf = "BEARISH", 64
        g_driver = "Gold faces short-term headwinds as firm dollar strength and Treasury yields cap immediate upside momentum."

    # Nasdaq Analysis
    if nq_chg > 0 and us10y_chg <= 0:
        nq_bias, nq_conf = "BULLISH", 84
        nq_driver = "Tech equities demonstrate strength with steady corporate sentiment and stable rate expectations easing valuation pressure on growth names."
    elif us10y_chg > 1.5 or nq_chg < 0:
        nq_bias, nq_conf = "BEARISH", 72
        nq_driver = "Higher Treasury yields and defensive rotation weigh on tech multiples, keeping buyers cautious in the near term."
    else:
        nq_bias, nq_conf = "NEUTRAL", 58
        nq_driver = "Nasdaq is trading within a defined intraday range as market participants wait for fresh mega-cap and macro drivers."

    # US30 Analysis
    if us30_chg >= 0:
        u_bias, u_conf = "BULLISH", 70
        u_driver = "Industrial and cyclical components display resilience, backed by steady broader economic indicators."
    else:
        u_bias, u_conf = "BEARISH", 66
        u_driver = "Cyclical stocks experience modest profit-taking amidst shifting commodity input costs and macroeconomic repricing."

    return {
        "mood": mood,
        "mood_summary": mood_summary,
        "biases": {
            "XAUUSD": {"bias": g_bias, "confidence": g_conf, "driver": g_driver},
            "NQ": {"bias": nq_bias, "confidence": nq_conf, "driver": nq_driver},
            "US30": {"bias": u_bias, "confidence": u_conf, "driver": u_driver}
        }
    }

# ---------------------------------------------------------
# 4. RENDER UI
# ---------------------------------------------------------
prices = get_live_prices()
news = fetch_web_news()
macro_data = generate_macro_synthesis(prices, news)

# Header
st.title("⚡ HybridTrader — AI Macro Desk")
st.caption(f"Your personal financial newspaper — powered by AI • Updated at **{now_est}**")
st.markdown("---")

# Main Content Layout
left_col, right_col = st.columns([1.65, 1.0])

# --- LEFT COLUMN: AI MACRO DESK ASSET CARDS ---
with left_col:
    st.markdown("### 📈 AI Macro Desk `Market bias analysis` ")
    
    asset_list = [
        ("XAUUSD", "XAUUSD (Gold)", prices.get("XAUUSD", {"price": 0, "change": 0})),
        ("NQ", "US100 / NQ (Nasdaq)", prices.get("NQ", {"price": 0, "change": 0})),
        ("US30", "US30 (Dow Jones)", prices.get("US30", {"price": 0, "change": 0}))
    ]
    
    for sym, label, p_data in asset_list:
        b_info = macro_data["biases"].get(sym, {"bias": "NEUTRAL", "confidence": 50, "driver": ""})
        bias_str = b_info["bias"].upper()
        conf = b_info["confidence"]
        driver_text = b_info["driver"]
        
        chg_val = p_data["change"]
        chg_class = "up" if chg_val >= 0 else "down"
        chg_str = f"{chg_val:+.2f}%"
        
        badge_class = f"badge-{bias_str.lower()}"
        
        # Render clean HTML directly using st.html
        st.html(f"""
        <div class="macro-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-name">{label}</span>
                <div>
                    <span class="price-text {chg_class}">{chg_str}</span>
                    <span class="badge {badge_class}">{bias_str}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.8rem; color: #94A3B8;">
                <span>Confidence</span>
                <span style="font-weight: 700; color: #E2E8F0;">{conf}%</span>
            </div>
            <div class="confidence-bg">
                <div class="confidence-fill" style="width: {conf}%;"></div>
            </div>
            <div class="ai-label">✨ AI Analysis</div>
            <div class="ai-desc">{driver_text}</div>
        </div>
        """)

# --- RIGHT COLUMN: MARKET MOOD & NEWS WIRE ---
with right_col:
    st.markdown("### 📊 Capital Flow & Market Mood")
    
    mood_val = macro_data["mood"].upper()
    mood_badge = "badge-bullish" if "ON" in mood_val else ("badge-bearish" if "OFF" in mood_val else "badge-neutral")
    
    st.html(f"""
    <div class="macro-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 1.05rem; font-weight: 700;">Market Environment</span>
            <span class="badge {mood_badge}">{mood_val}</span>
        </div>
        <p style="color: #CBD5E1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
            {macro_data["mood_summary"]}
        </p>
    </div>
    """)
    
    st.markdown("#### 📡 Breaking Headlines Wire")
    for headline in news:
        st.info(f"📰 {headline}")

st.markdown("---")

# --- BOTTOM SECTION: MACRO CORRELATION TRACKER ---
st.markdown("### 🔗 Macro Correlation Tracker (Daily Direction)")

c1, c2, c3, c4 = st.columns(4)
correlations = [
    ("DXY", "US Dollar Index", prices.get("DXY", {"price": 0, "change": 0})),
    ("US10Y", "10-Year US Yield", prices.get("US10Y", {"price": 0, "change": 0})),
    ("VIX", "Volatility Index (VIX)", prices.get("VIX", {"price": 0, "change": 0})),
    ("CL", "Crude Oil (WTI)", prices.get("CL", {"price": 0, "change": 0}))
]

for idx, (sym, label, p_data) in enumerate(correlations):
    col = [c1, c2, c3, c4][idx]
    with col:
        p = p_data["price"]
        c = p_data["change"]
        arrow = "▲" if c >= 0 else "▼"
        color = "#10B981" if c >= 0 else "#EF4444"
        
        st.html(f"""
        <div class="corr-card">
            <div style="font-size: 0.78rem; color: #94A3B8;">{label} ({sym})</div>
            <div style="font-size: 1.1rem; font-weight: 700; margin: 4px 0;">${p:,.2f}</div>
            <div style="color: {color}; font-weight: 700; font-size: 0.85rem;">{arrow} {c:+.2f}%</div>
        </div>
        """)
