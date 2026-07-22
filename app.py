import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLES
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

# Custom Dark Hybrid Design CSS
st.html("""
<style>
    /* Dark Base Theme */
    .stApp { 
        background-color: #080A0E; 
        color: #E2E8F0; 
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }
    
    /* Global Container Padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 95%;
    }

    /* Glass Cards */
    .macro-card {
        background: #11141C;
        border: 1px solid #1C2330;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    /* Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        display: inline-block;
    }
    .badge-bullish { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-bearish { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.4); }
    .badge-neutral { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.4); }

    /* Confidence Bar */
    .confidence-bg {
        width: 100%;
        background-color: #1A2230;
        border-radius: 4px;
        height: 5px;
        margin-top: 6px;
        margin-bottom: 16px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #10B981, #34D399);
    }

    /* Typography */
    .asset-title { font-size: 1.15rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.2px; }
    .price-text { font-size: 0.9rem; font-weight: 600; margin-right: 10px; }
    .up { color: #10B981; }
    .down { color: #EF4444; }
    .ai-label { font-size: 0.8rem; font-weight: 600; color: #38BDF8; margin-bottom: 6px; display: flex; align-items: center; gap: 5px; }
    .ai-desc { font-size: 0.88rem; color: #94A3B8; line-height: 1.55; font-weight: 400; }

    /* Bottom Ticker Bar */
    .bottom-ticker {
        background-color: #0D1117;
        border: 1px solid #1C2330;
        border-radius: 10px;
        padding: 14px 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-top: 20px;
    }
    .ticker-item { text-align: center; }
    .ticker-symbol { font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .ticker-price { font-size: 1.05rem; font-weight: 700; color: #F8FAFC; margin: 2px 0; }
    .ticker-chg { font-size: 0.82rem; font-weight: 700; }

    h1, h2, h3, h4 { color: #F8FAFC !important; }
</style>
""")

# ---------------------------------------------------------
# 2. REAL-TIME DATA SCRAPERS
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
            "Federal Reserve signals prolonged pause as inflation metrics moderate.",
            "Treasury yields retreat from daily highs amidst steady demand at auctions.",
            "Geopolitical tensions in key supply routes maintain baseline bid in commodities."
        ]

# ---------------------------------------------------------
# 3. AI MACRO & SYNTHESIS ENGINE
# ---------------------------------------------------------
def generate_macro_synthesis(prices, news):
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
            Act as an institutional macro chief trader. Synthesize detailed, deep fundamental rationales for XAUUSD, Nasdaq 100 (NQ), and Dow Jones (US30).
            Live Prices & % Changes: {prices}
            News Headlines: {news}
            
            Return JSON in exact structure:
            {{
                "mood": "RISK-OFF or RISK-ON or RISK-NEUTRAL",
                "mood_angle": 135,
                "investor_positioning": "Detailed paragraph explaining investor capital flow, flight-to-safety dynamics, and Treasury/Equity shifts.",
                "policy_outlook": "Detailed paragraph explaining global monetary policy, Federal Reserve stance, real yield direction, and inflation drivers.",
                "biases": {{
                    "XAUUSD": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 76, "driver": "2-3 sentence institutional explanation on safe-haven bid, real yield pressure, and DXY correlation."}},
                    "NQ": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 84, "driver": "2-3 sentence institutional explanation on growth stock multiples, tech earnings flow, and 10Y yield sensitivity."}},
                    "US30": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 68, "driver": "2-3 sentence institutional explanation on cyclical rotation, industrial performance, and macroeconomic pulse."}}
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

    # Built-in Deep Macro Engine (Fallback)
    dxy_chg = prices.get("DXY", {}).get("change", 0)
    us10y_chg = prices.get("US10Y", {}).get("change", 0)
    vix_chg = prices.get("VIX", {}).get("change", 0)
    nq_chg = prices.get("NQ", {}).get("change", 0)
    us30_chg = prices.get("US30", {}).get("change", 0)
    
    # Gauge angle computation: RISK-OFF (45deg), NEUTRAL (90deg), RISK-ON (135deg)
    if vix_chg > 2.5 or dxy_chg > 0.3:
        mood = "RISK-OFF"
        angle = 45
        pos = "Market sentiment is firmly defensive as investors actively reduce exposure to high-beta assets. Safe-haven capital flows are favoring precious metals and short-duration Treasuries as volatility ticks higher."
        pol = "Central bank policy remains under close scrutiny. Concerns over persistent inflation metrics and elevated borrowing costs continue to exert upward pressure on sovereign yields, dampening broader risk appetite."
    elif vix_chg < -2.0 and dxy_chg < 0:
        mood = "RISK-ON"
        angle = 135
        pos = "Institutional capital is aggressively rotating into growth and cyclical sectors. Lower volatility expectations and easing Dollar strength are encouraging momentum traders to expand long equity exposure."
        pol = "Macro policy expectations lean accommodating, with traders pricing in potential easing cycles. Moderating yields provide a supportive backdrop for corporate earnings expansion and risk asset appreciation."
    else:
        mood = "RISK-NEUTRAL"
        angle = 90
        pos = "Market participants are operating in a cautious consolidation phase. Capital is sitting on the sidelines pending incoming macroeconomic catalyst prints and corporate earnings reports."
        pol = "The global policy outlook reflects a balanced stance. Central banks maintain data-dependent guidance, creating an environment where asset classes react primarily to immediate micro news."

    # Gold Analysis
    if dxy_chg < 0 or us10y_chg < 0:
        g_bias, g_conf = "BULLISH", 78
        g_driver = "Safe-haven demand and moderating real yields are keeping strong bids under the metal. Softness in the US Dollar Index further enhances upside attraction for institutional allocators."
    else:
        g_bias, g_conf = "BEARISH", 65
        g_driver = "Firm Treasury yields and a resilient Dollar are capping gold's immediate upside momentum. Traders are exercising caution as elevated interest rates increase holding costs."

    # Nasdaq Analysis
    if nq_chg > 0 and us10y_chg <= 0:
        nq_bias, nq_conf = "BULLISH", 84
        nq_driver = "Growth equities demonstrate resilient buying pressure as stable Treasury yields relieve valuation multiples. Large-cap technology sentiment remains supported by consistent capital inflows."
    elif us10y_chg > 1.2 or nq_chg < 0:
        nq_bias, nq_conf = "BEARISH", 72
        nq_driver = "Higher benchmark yields continue to weigh on tech multiples, keeping buyers defensive. Geopolitical uncertainties and rate sensitivity maintain profit-taking pressure."
    else:
        nq_bias, nq_conf = "NEUTRAL", 60
        nq_driver = "Nasdaq trades within a structured intraday range as market participants await fresh macroeconomic data drivers and corporate earnings confirmations."

    # US30 Analysis
    if us30_chg >= 0:
        u_bias, u_conf = "BULLISH", 70
        u_driver = "Industrial and cyclical heavyweights exhibit steady baseline demand, buoyed by economic activity indicators and positive sector rotation."
    else:
        u_bias, u_conf = "BEARISH", 66
        u_driver = "Cyclical components face mild downside pressure as broader macro caution and shifting input costs drive short-term position trimming."

    return {
        "mood": mood,
        "mood_angle": angle,
        "investor_positioning": pos,
        "policy_outlook": pol,
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
macro = generate_macro_synthesis(prices, news)

# Header Section
st.title("Good afternoon, Trader.")
st.caption(f"⚡ Global economic chaos, turned into clarity • Auto-Updated at **{now_est}**")
st.markdown("---")

# Main Content Grid
left_col, right_col = st.columns([1.6, 1.1])

# --- LEFT COLUMN: AI MACRO DESK ASSET CARDS ---
with left_col:
    st.markdown("### 📈 AI Macro Desk `Market bias analysis` ")
    
    asset_list = [
        ("XAUUSD", "XAUUSD (Gold)", prices.get("XAUUSD", {"price": 0, "change": 0})),
        ("NQ", "US100 / NQ (Nasdaq)", prices.get("NQ", {"price": 0, "change": 0})),
        ("US30", "US30 (Dow Jones)", prices.get("US30", {"price": 0, "change": 0}))
    ]
    
    for sym, label, p_data in asset_list:
        b_info = macro["biases"].get(sym, {"bias": "NEUTRAL", "confidence": 50, "driver": ""})
        bias_str = b_info["bias"].upper()
        conf = b_info["confidence"]
        driver_text = b_info["driver"]
        
        chg_val = p_data["change"]
        chg_class = "up" if chg_val >= 0 else "down"
        chg_str = f"{chg_val:+.2f}%"
        badge_class = f"badge-{bias_str.lower()}"
        
        st.html(f"""
        <div class="macro-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-title">{label}</span>
                <div>
                    <span class="price-text {chg_class}">{chg_str}</span>
                    <span class="badge {badge_class}">{bias_str}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.8rem; color: #64748B;">
                <span>Confidence</span>
                <span style="font-weight: 700; color: #E2E8F0;">{conf}%</span>
            </div>
            <div class="confidence-bg">
                <div class="confidence-fill" style="width: {conf}%;"></div>
            </div>
            <div class="ai-label">✨ AI Fundamental Analysis</div>
            <div class="ai-desc">{driver_text}</div>
        </div>
        """)

# --- RIGHT COLUMN: MARKET MOOD (GAUGE) & POLICY OUTLOOK ---
with right_col:
    st.markdown("### 📊 Market Mood & Policy Desk")
    
    mood_val = macro["mood"]
    badge_color = "#10B981" if "ON" in mood_val else ("#EF4444" if "OFF" in mood_val else "#F59E0B")
    angle = macro.get("mood_angle", 90)
    
    # Dynamic SVG Dial Gauge
    gauge_svg = f"""
    <svg width="180" height="100" viewBox="0 0 180 100" style="display: block; margin: 0 auto;">
        <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1E293B" stroke-width="14" stroke-linecap="round" />
        <path d="M 20 90 A 70 70 0 0 1 65 28" fill="none" stroke="#EF4444" stroke-width="14" stroke-linecap="round" />
        <path d="M 65 28 A 70 70 0 0 1 115 28" fill="none" stroke="#F59E0B" stroke-width="14" />
        <path d="M 115 28 A 70 70 0 0 1 160 90" fill="none" stroke="#10B981" stroke-width="14" stroke-linecap="round" />
        <g transform="translate(90, 90) rotate({angle})">
            <line x1="0" y1="0" x2="-55" y2="0" stroke="#F8FAFC" stroke-width="3" stroke-linecap="round" />
            <circle cx="0" cy="0" r="5" fill="#F8FAFC" />
        </g>
    </svg>
    """
    
    st.html(f"""
    <div class="macro-card">
        <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin-bottom: 12px;">
            Investor Positioning
        </div>
        <div style="display: flex; gap: 16px; align-items: center;">
            <div style="flex: 1; text-align: center;">
                {gauge_svg}
                <div style="font-size: 0.85rem; font-weight: 800; color: {badge_color}; margin-top: 6px; letter-spacing: 0.5px;">
                    {mood_val}
                </div>
            </div>
            <div style="flex: 1.8; font-size: 0.86rem; color: #94A3B8; line-height: 1.5;">
                {macro["investor_positioning"]}
            </div>
        </div>
    </div>
    
    <div class="macro-card">
        <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;">
            Global Economic Outlook
        </div>
        <div style="font-size: 0.86rem; color: #94A3B8; line-height: 1.5;">
            {macro["policy_outlook"]}
        </div>
    </div>
    """)

st.markdown("---")

# --- BOTTOM TICKER BAR: CORRELATION ASSETS ---
st.markdown("### 🔗 Institutional Correlation Tracker")

correlations = [
    ("DXY", "US Dollar Index", prices.get("DXY", {"price": 0, "change": 0})),
    ("US10Y", "10-Year US Yield", prices.get("US10Y", {"price": 0, "change": 0})),
    ("VIX", "Volatility Index", prices.get("VIX", {"price": 0, "change": 0})),
    ("CL", "Crude Oil (WTI)", prices.get("CL", {"price": 0, "change": 0}))
]

ticker_items_html = ""
for sym, label, p_data in correlations:
    p = p_data["price"]
    c = p_data["change"]
    arrow = "▲" if c >= 0 else "▼"
    color = "#10B981" if c >= 0 else "#EF4444"
    
    ticker_items_html += f"""
    <div class="ticker-item">
        <div class="ticker-symbol">{label} ({sym})</div>
        <div class="ticker-price">${p:,.2f}</div>
        <div class="ticker-chg" style="color: {color};">{arrow} {c:+.2f}%</div>
    </div>
    """

st.html(f"""
<div class="bottom-ticker">
    {ticker_items_html}
</div>
""")
