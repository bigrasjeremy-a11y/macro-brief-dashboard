import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. PAGE SETUP & THEME STYLING
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

# Precise CSS Styling to match HybridTrader (Image 1)
st.html("""
<style>
    /* Dark Slate App Background */
    .stApp { 
        background-color: #0B0E11; 
        color: #E2E8F0; 
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }
    
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 96%;
    }

    /* Container Box Styling */
    .macro-container {
        background-color: #12151B;
        border: 1px solid #1C222C;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Asset Card Inner Styling */
    .asset-card {
        background-color: #171B24;
        border: 1px solid #222936;
        border-radius: 10px;
        padding: 16px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* Badges */
    .badge {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-bullish { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-bearish { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-neutral { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }

    /* Confidence Bar */
    .confidence-bg {
        width: 100%;
        background-color: #222A38;
        border-radius: 4px;
        height: 4px;
        margin-top: 4px;
        margin-bottom: 12px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        background: #10B981;
    }

    /* Typography */
    .asset-title { font-size: 1.05rem; font-weight: 700; color: #FFFFFF; }
    .price-text { font-size: 0.85rem; font-weight: 600; margin-right: 6px; }
    .up { color: #10B981; }
    .down { color: #EF4444; }
    .ai-label { font-size: 0.78rem; font-weight: 600; color: #38BDF8; margin-bottom: 4px; display: flex; align-items: center; gap: 4px; }
    .ai-desc { font-size: 0.82rem; color: #94A3B8; line-height: 1.45; }

    /* Flow Bar Chart Layout */
    .flow-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        font-size: 0.78rem;
    }
    .flow-label { width: 60px; font-weight: 700; color: #94A3B8; }
    .flow-bar-container { flex-grow: 1; height: 12px; background: #1A212D; border-radius: 3px; position: relative; margin: 0 10px; }
    .flow-val { width: 50px; text-align: right; font-weight: 700; }

    /* Bottom Ticker */
    .bottom-ticker {
        background-color: #12151B;
        border: 1px solid #1C222C;
        border-radius: 10px;
        padding: 12px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .ticker-item { text-align: center; }
    .ticker-symbol { font-size: 0.75rem; color: #64748B; font-weight: 600; }
    .ticker-price { font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin: 2px 0; }
    .ticker-chg { font-size: 0.8rem; font-weight: 700; }

    h1, h2, h3, h4 { color: #F8FAFC !important; }
</style>
""")

# ---------------------------------------------------------
# 2. MARKET DATA & SCRAPERS
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
            "Federal Reserve signals cautious policy trajectory amidst shifting economic data.",
            "US Treasury Yields flatten as market digests inflation and labor market metrics.",
            "Equity index futures consolidate in pre-market trading following earnings announcements."
        ]

# ---------------------------------------------------------
# 3. AI MACRO ENGINE (DEEP NARRATIVES)
# ---------------------------------------------------------
def generate_macro_synthesis(prices, news):
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
            Synthesize rich institutional macro narratives for Gold (XAUUSD), Nasdaq 100 (NQ), and Dow Jones (US30).
            Prices: {prices}
            News: {news}
            
            Output JSON format:
            {{
                "headline": "Punchy 8-word market headline summarizing today's flow",
                "narrative": "Detailed 4-sentence institutional analysis detailing session momentum, yields, dollar pressure, and risk appetite.",
                "mood": "RISK-ON or RISK-OFF or RISK-NEUTRAL",
                "biases": {{
                    "US30": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 70, "driver": "Detailed 3-sentence fundamental rationale regarding labor data, corporate earnings, and soft-landing narrative."}},
                    "NQ": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 84, "driver": "Detailed 3-sentence fundamental rationale covering tech leadership, valuation multiples, and Treasury yield pressure."}},
                    "XAUUSD": {{"bias": "BULLISH/BEARISH/NEUTRAL", "confidence": 78, "driver": "Detailed 3-sentence fundamental rationale on safe-haven demand, Middle East geopolitical risk, and real yields."}}
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

    # Built-in Dynamic Fallback Macro Engine
    dxy_chg = prices.get("DXY", {}).get("change", 0)
    us10y_chg = prices.get("US10Y", {}).get("change", 0)
    vix_chg = prices.get("VIX", {}).get("change", 0)
    nq_chg = prices.get("NQ", {}).get("change", 0)
    us30_chg = prices.get("US30", {}).get("change", 0)
    
    if vix_chg > 2.0 or dxy_chg > 0.3:
        mood = "RISK-OFF"
        headline = "Yields and Dollar Take Control While Equities Face Headwinds"
        narrative = "The tape is leaning defensive as US 10-year yields and the Dollar Index both push higher, putting pressure on risk assets. Despite commodity resilience, broader index futures are staying cautious due to lingering macroeconomic uncertainties and interest rate positioning."
    elif vix_chg < -1.5 and dxy_chg < 0:
        mood = "RISK-ON"
        headline = "Tech Leads the Charge While Safe Havens Take a Backseat"
        narrative = "US equities are kicking off with a clear appetite for growth risk, with the NASDAQ 100 pushing higher ahead of major corporate earnings. A softening US Dollar and moderating yields provide key tailwinds across broader market sectors."
    else:
        mood = "RISK-NEUTRAL"
        headline = "Markets Consolidate as Traders Await Fresh Macro Catalysts"
        narrative = "Price action across major indices remains range-bound as institutional traders digest conflicting economic prints. Yields are holding steady while participants position around key technical support levels ahead of upcoming central bank speakers."

    # US30 Analysis
    if us30_chg >= 0:
        u_bias, u_conf = "BULLISH", 70
        u_driver = "Dow breaches key intraday levels on resilient labor data, bolstering the soft landing narrative. Industrial heavyweights show steady baseline demand, though volatile input costs from commodity channels remain a secondary factor."
    else:
        u_bias, u_conf = "BEARISH", 68
        u_driver = "Higher benchmark yields and elevated input costs keep buyers defensive across industrial constituents. Heavyweight components require stronger catalyst confirmation to reverse the intraday pullback."

    # Nasdaq Analysis
    if nq_chg > 0 and us10y_chg <= 0:
        nq_bias, nq_conf = "BULLISH", 84
        nq_driver = "Tech leads the market higher as earnings resilience reinforces a bullish outlook, breaking recent consolidation. Growth multiples are expanding despite rising 10-year Treasury yields looming in the background."
    else:
        nq_bias, nq_conf = "BEARISH", 72
        nq_driver = "Hawkish Fed commentary and elevated real yields keep tech multiples under pressure. Sector rotation out of growth into defensive havens continues to cap immediate upside."

    # Gold Analysis
    if dxy_chg < 0 or us10y_chg < 0:
        g_bias, g_conf = "BULLISH", 78
        g_driver = "Middle East tensions and underlying recession concerns push capital toward safe havens. Gold holds critical technical support while softer inflation expectations reinforce a strong baseline bid."
    else:
        g_bias, g_conf = "BEARISH", 64
        g_driver = "Gold faces near-term friction as firm dollar index performance and Treasury yields cap upside breakout attempts. Safe-haven inflows offer a partial offset against rate pressures."

    return {
        "headline": headline,
        "narrative": narrative,
        "mood": mood,
        "biases": {
            "US30": {"bias": u_bias, "confidence": u_conf, "driver": u_driver},
            "NQ": {"bias": nq_bias, "confidence": nq_conf, "driver": nq_driver},
            "XAUUSD": {"bias": g_bias, "confidence": g_conf, "driver": g_driver}
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
st.caption("⚡ Your personal financial newspaper — powered by AI")

st.markdown("---")

# Main Split Grid (Left: 2x2 AI Desk | Right: For You & Capital Flow)
col_left, col_right = st.columns([1.65, 1.0])

# --- LEFT COLUMN: AI MACRO DESK (2x2 GRID) ---
with col_left:
    st.html("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-size: 1.1rem; font-weight: 700;">📈 AI Macro Desk <span style="font-size: 0.8rem; font-weight: 400; color: #64748B;">Market bias analysis</span></span>
    </div>
    """)
    
    # Row 1: US30 & US100 (NQ)
    r1_c1, r1_c2 = st.columns(2)
    
    with r1_c1:
        u_info = macro["biases"].get("US30", {"bias": "BULLISH", "confidence": 70, "driver": ""})
        u_chg = prices.get("US30", {}).get("change", 0)
        u_class = "up" if u_chg >= 0 else "down"
        u_badge = f"badge-{u_info['bias'].lower()}"
        
        st.html(f"""
        <div class="asset-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-title">US30</span>
                <div>
                    <span class="price-text {u_class}">{u_chg:+.2f}%</span>
                    <span class="badge {u_badge}">{u_info['bias']}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.75rem; color: #64748B;">
                <span>Confidence</span>
                <span style="font-weight: 700; color: #E2E8F0;">{u_info['confidence']}%</span>
            </div>
            <div class="confidence-bg">
                <div class="confidence-fill" style="width: {u_info['confidence']}%;"></div>
            </div>
            <div class="ai-label">✨ AI Analysis</div>
            <div class="ai-desc">{u_info['driver']}</div>
        </div>
        """)
        
    with r1_c2:
        nq_info = macro["biases"].get("NQ", {"bias": "BULLISH", "confidence": 84, "driver": ""})
        nq_chg = prices.get("NQ", {}).get("change", 0)
        nq_class = "up" if nq_chg >= 0 else "down"
        nq_badge = f"badge-{nq_info['bias'].lower()}"
        
        st.html(f"""
        <div class="asset-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-title">US100</span>
                <div>
                    <span class="price-text {nq_class}">{nq_chg:+.2f}%</span>
                    <span class="badge {nq_badge}">{nq_info['bias']}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.75rem; color: #64748B;">
                <span>Confidence</span>
                <span style="font-weight: 700; color: #E2E8F0;">{nq_info['confidence']}%</span>
            </div>
            <div class="confidence-bg">
                <div class="confidence-fill" style="width: {nq_info['confidence']}%;"></div>
            </div>
            <div class="ai-label">✨ AI Analysis</div>
            <div class="ai-desc">{nq_info['driver']}</div>
        </div>
        """)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # Row 2: XAUUSD & DXY Correlation Note
    r2_c1, r2_c2 = st.columns(2)
    
    with r2_c1:
        g_info = macro["biases"].get("XAUUSD", {"bias": "BULLISH", "confidence": 78, "driver": ""})
        g_chg = prices.get("XAUUSD", {}).get("change", 0)
        g_class = "up" if g_chg >= 0 else "down"
        g_badge = f"badge-{g_info['bias'].lower()}"
        
        st.html(f"""
        <div class="asset-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-title">XAUUSD</span>
                <div>
                    <span class="price-text {g_class}">{g_chg:+.2f}%</span>
                    <span class="badge {g_badge}">{g_info['bias']}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.75rem; color: #64748B;">
                <span>Confidence</span>
                <span style="font-weight: 700; color: #E2E8F0;">{g_info['confidence']}%</span>
            </div>
            <div class="confidence-bg">
                <div class="confidence-fill" style="width: {g_info['confidence']}%;"></div>
            </div>
            <div class="ai-label">✨ AI Analysis</div>
            <div class="ai-desc">{g_info['driver']}</div>
        </div>
        """)
        
    with r2_c2:
        d_chg = prices.get("DXY", {}).get("change", 0)
        d_class = "up" if d_chg >= 0 else "down"
        
        st.html(f"""
        <div class="asset-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="asset-title">DXY (US Dollar)</span>
                <div>
                    <span class="price-text {d_class}">{d_chg:+.2f}%</span>
                    <span class="badge badge-neutral">CORRELATION</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.75rem; color: #64748B;">
                <span>Impact Index</span>
                <span style="font-weight: 700; color: #E2E8F0;">HIGH</span>
            </div>
            <div class="confidence-bg">
                <div class="confidence-fill" style="width: 85%;"></div>
            </div>
            <div class="ai-label">✨ AI Analysis</div>
            <div class="ai-desc">The US Dollar Index serves as a primary macro anchor across equities and precious metals. Dollar strength directly caps gold upside while tightening global liquidity conditions.</div>
        </div>
        """)

# --- RIGHT COLUMN: FOR YOU & CAPITAL FLOW BAR CHART ---
with col_right:
    mood_str = macro["mood"]
    mood_badge = "badge-bullish" if "ON" in mood_str else ("badge-bearish" if "OFF" in mood_str else "badge-neutral")
    
    st.html(f"""
    <div class="macro-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-weight: 700; font-size: 1.05rem;">📰 For You</span>
            <span class="badge {mood_badge}">Mood: {mood_str}</span>
        </div>
        <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">
            {macro['headline']}
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5; margin-bottom: 20px;">
            {macro['narrative']}
        </div>
        
        <div style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
            <span>📊 Capital Flow</span>
            <span style="font-size: 0.72rem; color: #10B981; font-weight: 600;">● Live</span>
        </div>
    </div>
    """)
    
    # Capital Flow Horizontal Visual Bar Chart
    flow_assets = [
        ("US10Y", prices.get("US10Y", {}).get("change", 0)),
        ("US100", prices.get("NQ", {}).get("change", 0)),
        ("US30", prices.get("US30", {}).get("change", 0)),
        ("DXY", prices.get("DXY", {}).get("change", 0)),
        ("XAUUSD", prices.get("XAUUSD", {}).get("change", 0)),
        ("VIX", prices.get("VIX", {}).get("change", 0)),
        ("CRUDE", prices.get("CL", {}).get("change", 0))
    ]
    
    flow_html = "<div class='macro-container' style='margin-top: -10px;'>"
    for sym, val in flow_assets:
        color = "#10B981" if val >= 0 else "#EF4444"
        width = min(abs(val) * 35, 100)
        
        flow_html += f"""
        <div class="flow-row">
            <div class="flow-label">{sym}</div>
            <div class="flow-bar-container">
                <div style="width: {width}%; height: 100%; background-color: {color}; border-radius: 2px;"></div>
            </div>
            <div class="flow-val" style="color: {color};">{val:+.2f}%</div>
        </div>
        """
    flow_html += "</div>"
    st.html(flow_html)

st.markdown("---")

# --- BOTTOM SECTION: CORRELATION TRACKER ---
st.markdown("### 🔗 Daily Correlation Tracker")

correlations = [
    ("DXY", "US Dollar Index", prices.get("DXY", {"price": 0, "change": 0})),
    ("US10Y", "10-Year Yield", prices.get("US10Y", {"price": 0, "change": 0})),
    ("VIX", "Volatility Index", prices.get("VIX", {"price": 0, "change": 0})),
    ("CL", "Crude Oil WTI", prices.get("CL", {"price": 0, "change": 0}))
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
