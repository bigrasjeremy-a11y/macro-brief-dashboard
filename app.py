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
# 1. PAGE SETUP & AUTO-REFRESH
# ---------------------------------------------------------
st.set_page_config(
    page_title="HybridTrader - Macro Desk",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto-refresh app silently every 60 seconds
st_autorefresh(interval=60000, limit=None, key="macro_auto_refresh")

# Enforce Eastern Time Zone (EST / NY Time)
est_tz = pytz.timezone('America/New_York')
now_est = datetime.datetime.now(est_tz).strftime("%H:%M:%S EST")

# Custom CSS matching the exact HybridTrader UI theme in the image
st.markdown("""
    <style>
        /* Base Dark Theme */
        .stApp { background-color: #0D0F12; color: #E2E8F0; font-family: 'Inter', sans-serif; }
        
        /* Glassmorphic Dark Cards */
        .macro-card {
            background-color: #13171D;
            border: 1px solid #1E232B;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        
        /* Badges */
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            display: inline-block;
        }
        .badge-bullish { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid #10B981; }
        .badge-bearish { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid #EF4444; }
        .badge-neutral { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid #F59E0B; }
        
        /* Progress Bar for Confidence */
        .confidence-container {
            width: 100%;
            background-color: #1E232B;
            border-radius: 6px;
            height: 6px;
            margin-top: 8px;
            margin-bottom: 14px;
        }
        .confidence-fill {
            height: 100%;
            border-radius: 6px;
            background: linear-gradient(90deg, #10B981, #34D399);
        }
        
        /* Typography */
        .asset-title { font-size: 1.25rem; font-weight: 700; color: #FFFFFF; }
        .asset-price { font-size: 0.9rem; font-weight: 600; }
        .price-up { color: #10B981; }
        .price-down { color: #EF4444; }
        .ai-header { font-size: 0.8rem; font-weight: 600; color: #38BDF8; margin-bottom: 4px; }
        .ai-text { font-size: 0.88rem; color: #94A3B8; line-height: 1.45; }
        
        /* Correlation Bar */
        .corr-item {
            background-color: #13171D;
            border: 1px solid #1E232B;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        h1, h2, h3, h4 { color: #F8FAFC !important; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. REAL-TIME DATA FETCHING (yfinance & Web RSS)
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def get_live_prices():
    """Fetches real-time price changes for Focus Assets & Correlations"""
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
    """Pulls breaking economic news via RSS"""
    try:
        url = "https://news.google.com/rss/search?q=forex+economy+fed+inflation+when:1d&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")[:6]
        return [item.title.text for item in items]
    except Exception:
        return ["Fed officials remain cautious ahead of inflation prints.", "US Dollar consolidates amidst rate expectations."]

# ---------------------------------------------------------
# 3. AI MACRO ENGINE (GPT-4o API Synthesis)
# ---------------------------------------------------------
def analyze_macro_with_ai(news_list, prices):
    """Sends prices & news to GPT-4o to dynamically compute confidence %, biases, and rationale"""
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    if not api_key:
        return {
            "mood": "RISK-NEUTRAL",
            "mood_type": "neutral",
            "mood_driver": "Add OPENAI_API_KEY to Streamlit Secrets to enable full AI macro synthesis.",
            "biases": {
                "XAUUSD": {"bias": "NEUTRAL", "confidence": 50, "driver": "Awaiting API key integration."},
                "NQ": {"bias": "NEUTRAL", "confidence": 50, "driver": "Awaiting API key integration."},
                "US30": {"bias": "NEUTRAL", "confidence": 50, "driver": "Awaiting API key integration."}
            }
        }
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    You are an institutional macro strategist analyzing market bias for Gold (XAUUSD), Nasdaq 100 (NQ), and Dow Jones (US30).
    
    Current Web News: {news_list}
    Current Asset Prices & % Changes: {prices}
    
    Synthesize these data points and output JSON ONLY in this exact structure:
    {{
        "mood": "RISK-ON, RISK-OFF, or RISK-NEUTRAL",
        "mood_driver": "2-3 sentences providing an executive summary of capital flows and overall market sentiment.",
        "biases": {{
            "XAUUSD": {{
                "bias": "BULLISH/BEARISH/NEUTRAL",
                "confidence": 78,
                "driver": "1-2 concise sentences explaining the institutional driver (e.g. rate cut expectations, real yields, safe-haven demand)."
            }},
            "NQ": {{
                "bias": "BULLISH/BEARISH/NEUTRAL",
                "confidence": 84,
                "driver": "1-2 concise sentences explaining the institutional driver (e.g. tech valuation pressure, treasury yields, earnings sentiment)."
            }},
            "US30": {{
                "bias": "BULLISH/BEARISH/NEUTRAL",
                "confidence": 68,
                "driver": "1-2 concise sentences explaining the institutional driver (e.g. industrial rotation, cyclical economic health)."
            }}
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
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "mood": "NEUTRAL",
            "mood_driver": f"Error running AI analysis: {str(e)}",
            "biases": {
                "XAUUSD": {"bias": "NEUTRAL", "confidence": 50, "driver": "Error analyzing market data."},
                "NQ": {"bias": "NEUTRAL", "confidence": 50, "driver": "Error analyzing market data."},
                "US30": {"bias": "NEUTRAL", "confidence": 50, "driver": "Error analyzing market data."}
            }
        }

# ---------------------------------------------------------
# 4. RENDER UI
# ---------------------------------------------------------
prices = get_live_prices()
news = fetch_web_news()
ai_res = analyze_macro_with_ai(news, prices)

# Top Bar Header
st.title("⚡ HybridTrader — AI Macro Desk")
st.caption(f"Personal Financial Newspaper • Auto-Updated at **{now_est}**")

st.markdown("---")

# Main Dashboard Layout (Left: AI Macro Desk Cards | Right: Capital Flow / Market Mood)
col_desk, col_flow = st.columns([1.6, 1.0])

# --- LEFT COLUMN: AI MACRO DESK ASSET CARDS ---
with col_desk:
    st.markdown("### 📈 AI Macro Desk `Market bias analysis` ")
    
    # Render Asset Cards: Gold, Nasdaq, Dow
    assets_info = [
        ("XAUUSD", "XAUUSD (Gold)", prices.get("XAUUSD", {"price": 0, "change": 0})),
        ("NQ", "US100 / NQ (Nasdaq)", prices.get("NQ", {"price": 0, "change": 0})),
        ("US30", "US30 (Dow Jones)", prices.get("US30", {"price": 0, "change": 0}))
    ]
    
    for sym, label, p_data in assets_info:
        bias_info = ai_res.get("biases", {}).get(sym, {"bias": "NEUTRAL", "confidence": 50, "driver": "Analyzing..."})
        bias_str = bias_info.get("bias", "NEUTRAL").upper()
        badge_class = f"badge-{bias_str.lower()}"
        conf = bias_info.get("confidence", 50)
        
        chg_val = p_data["change"]
        chg_class = "price-up" if chg_val >= 0 else "price-down"
        chg_str = f"{chg_val:+.2f}%"
        
        st.markdown(f"""
        <div class="macro-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-title">{label}</span>
                <div>
                    <span class="asset-price {chg_class}" style="margin-right: 8px;">{chg_str}</span>
                    <span class="badge {badge_class}">{bias_str}</span>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.8rem; color: #94A3B8;">
                <span>Confidence</span>
                <span style="font-weight: 700; color: #E2E8F0;">{conf}%</span>
            </div>
            <div class="confidence-container">
                <div class="confidence-fill" style="width: {conf}%;"></div>
            </div>
            
            <div class="ai-header">✨ AI Analysis</div>
            <div class="ai-text">{bias_info.get('driver')}</div>
        </div>
        """, unsafe_allow_html=True)

# --- RIGHT COLUMN: CAPITAL FLOW & MARKET MOOD ---
with col_flow:
    st.markdown("### 📊 Capital Flow & Market Mood")
    
    mood_val = ai_res.get("mood", "RISK-NEUTRAL").upper()
    mood_badge = "badge-bullish" if "ON" in mood_val else ("badge-bearish" if "OFF" in mood_val else "badge-neutral")
    
    st.markdown(f"""
    <div class="macro-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 1.1rem; font-weight: 700;">Market Environment</span>
            <span class="badge {mood_badge}">{mood_val}</span>
        </div>
        <p style="color: #CBD5E1; font-size: 0.92rem; line-height: 1.5;">
            {ai_res.get("mood_driver")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # News Wire
    st.markdown("#### 📡 Breaking Market Headlines")
    for news_headline in news[:4]:
        st.caption(f"📰 {news_headline}")

st.markdown("---")

# --- BOTTOM SECTION: CORRELATION TRACKER ---
st.markdown("### 🔗 Macro Correlation Tracker (Daily Direction)")

corr_cols = st.columns(4)

correlations = [
    ("DXY", "US Dollar Index", prices.get("DXY", {"price": 0, "change": 0})),
    ("US10Y", "10-Year US Yield", prices.get("US10Y", {"price": 0, "change": 0})),
    ("VIX", "Volatility Index (VIX)", prices.get("VIX", {"price": 0, "change": 0})),
    ("CL", "Crude Oil (WTI)", prices.get("CL", {"price": 0, "change": 0}))
]

for idx, (sym, label, p_data) in enumerate(correlations):
    with corr_cols[idx]:
        p = p_data["price"]
        c = p_data["change"]
        arrow = "▲" if c >= 0 else "▼"
        color = "#10B981" if c >= 0 else "#EF4444"
        
        st.markdown(f"""
        <div class="corr-item">
            <div style="font-size: 0.8rem; color: #94A3B8;">{label} ({sym})</div>
            <div style="font-size: 1.1rem; font-weight: 700; margin: 4px 0;">${p:,.2f}</div>
            <div style="color: {color}; font-weight: 700; font-size: 0.88rem;">
                {arrow} {c:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
