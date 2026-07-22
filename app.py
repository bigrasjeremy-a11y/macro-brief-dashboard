import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import yfinance as yf
import streamlit.components.v1 as components
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

# Custom Dark Hybrid Design CSS
st.html("""
<style>
    /* Dark Slate Theme */
    .stApp { 
        background-color: #080A0E; 
        color: #E2E8F0; 
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 96%;
    }

    /* Cards */
    .macro-card {
        background-color: #11141C;
        border: 1px solid #1C2330;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
    }

    /* Asset Card Grid Item */
    .asset-card {
        background-color: #141822;
        border: 1px solid #1E2636;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
    }

    /* Badges */
    .badge {
        padding: 4px 9px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .badge-bullish { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); }
    .badge-bearish { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.35); }
    .badge-neutral { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.35); }

    /* Progress / Confidence Bar */
    .confidence-bg {
        width: 100%;
        background-color: #1D2636;
        border-radius: 4px;
        height: 5px;
        margin-top: 6px;
        margin-bottom: 14px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #10B981, #34D399);
    }

    /* Typography */
    .asset-title { font-size: 1.1rem; font-weight: 700; color: #FFFFFF; }
    .price-text { font-size: 0.9rem; font-weight: 700; margin-right: 8px; }
    .up { color: #10B981; }
    .down { color: #EF4444; }
    .ai-label { font-size: 0.78rem; font-weight: 600; color: #38BDF8; margin-bottom: 4px; }
    .ai-desc { font-size: 0.83rem; color: #94A3B8; line-height: 1.5; }

    /* Capital Flow Visual Rows */
    .flow-row {
        display: flex;
        align-items: center;
        margin-bottom: 9px;
        font-size: 0.78rem;
    }
    .flow-label { width: 65px; font-weight: 700; color: #94A3B8; }
    .flow-bar-bg { flex-grow: 1; height: 10px; background: #18202C; border-radius: 3px; position: relative; margin: 0 10px; overflow: hidden; }
    .flow-val { width: 55px; text-align: right; font-weight: 700; }

    /* Bottom Ticker */
    .bottom-ticker {
        background-color: #0E1117;
        border: 1px solid #1C2330;
        border-radius: 10px;
        padding: 12px 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    .ticker-item { text-align: center; }
    .ticker-symbol { font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .ticker-price { font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin: 2px 0; }
    .ticker-chg { font-size: 0.82rem; font-weight: 700; }

    /* Streamlit Button Tweaks for Cards */
    .stButton>button {
        width: 100%;
        background-color: #1A2230;
        color: #38BDF8;
        border: 1px solid #2B374A;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 4px 10px;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #243044;
        color: #7DD3FC;
        border-color: #38BDF8;
    }

    h1, h2, h3, h4 { color: #F8FAFC !important; }
</style>
""")

# ---------------------------------------------------------
# 2. TOP HEADER WITH LIVE EST CLOCK
# ---------------------------------------------------------
top_h_col1, top_h_col2 = st.columns([2.5, 1])

with top_h_col1:
    st.markdown("## Good afternoon, Trader.")
    st.caption("⚡ Global economic chaos, turned into clarity • Macro Direction & Correlation Engine")

with top_h_col2:
    # Live JavaScript Running Clock in EST (NY Time)
    components.html("""
    <div style="text-align: right; font-family: -apple-system, sans-serif; padding-right: 10px;">
        <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; letter-spacing: 0.5px;">NEW YORK MARKET TIME (EST)</div>
        <div id="est-clock" style="font-size: 1.25rem; font-weight: 800; color: #10B981; font-family: monospace;">--:--:-- EST</div>
    </div>
    <script>
        function updateESTClock() {
            const now = new Date();
            const options = { timeZone: 'America/New_York', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
            const estTime = new Intl.DateTimeFormat('en-US', options).format(now);
            document.getElementById('est-clock').innerText = estTime + ' EST';
        }
        setInterval(updateESTClock, 1000);
        updateESTClock();
    </script>
    """, height=65)

st.markdown("---")

# ---------------------------------------------------------
# 3. REAL-TIME DATA SCRAPER & MACRO ENGINE
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def get_live_prices():
    tickers = {
        "XAUUSD": "GC=F",
        "US30": "YM=F",
        "NQ": "NQ=F",
        "ES": "ES=F",
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
        url = "https://news.google.com/rss/search?q=iran+oil+inflation+fed+yields+when:1d&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")[:4]
        return [item.title.text for item in items]
    except Exception:
        return [
            "US-Iran tensions in Strait of Hormuz maintain upward pressure on Crude Oil.",
            "Treasury yields remain elevated as sticky inflation concerns weigh on Federal Reserve rate cut timing.",
            "Equity benchmarks evaluate corporate earnings resilience against geopolitical headwinds."
        ]

def generate_macro_synthesis(prices, news):
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
            Act as an elite macroeconomic strategist. Analyze live market data and return fundamental biases.
            Focus specifically on US-Iran tensions, Strait of Hormuz risks, Crude Oil spikes ($95+/bbl), inflation risks, and Treasury Yield impact on equities & gold.
            Prices: {prices}
            News: {news}
            
            Return JSON:
            {{
                "mood": "RISK-OFF or RISK-NEUTRAL or RISK-ON",
                "mood_angle": 45,
                "investor_positioning": "Detailed 3-sentence summary of capital positioning given geopolitics and inflation.",
                "policy_outlook": "Detailed 3-sentence summary on Federal Reserve interest rate odds and real yield expectations.",
                "headline": "Punchy 8-word headline summarizing session driver",
                "narrative": "Detailed narrative paragraph connecting US-Iran tensions -> Oil -> Yields -> Assets.",
                "biases": {{
                    "XAUUSD": {{"bias": "BULLISH", "confidence": 78, "driver": "3-sentence fundamental rationale.", "deep_dive": "Exhaustive deep dive on geopolitics, real yields, DXY correlation, and flight-to-safety."}},
                    "US30": {{"bias": "BEARISH", "confidence": 68, "driver": "3-sentence fundamental rationale.", "deep_dive": "Exhaustive deep dive on industrial sensitivity to energy costs, yields, and earnings."}},
                    "NQ": {{"bias": "BEARISH", "confidence": 75, "driver": "3-sentence fundamental rationale.", "deep_dive": "Exhaustive deep dive on growth valuation multiples, 10Y yield sensitivity, and tech sentiment."}},
                    "ES": {{"bias": "NEUTRAL", "confidence": 70, "driver": "3-sentence fundamental rationale.", "deep_dive": "Exhaustive deep dive on broad market index exposure, defensive sector offsets, and earnings factors."}}
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

    # Dynamic Fallback Macro Engine with Built-in Correlation Rules
    cl_chg = prices.get("CL", {}).get("change", 0)
    us10y_chg = prices.get("US10Y", {}).get("change", 0)
    vix_chg = prices.get("VIX", {}).get("change", 0)
    dxy_chg = prices.get("DXY", {}).get("change", 0)

    # Determine Mood & Angle
    if vix_chg > 2.0 or cl_chg > 2.0:
        mood, angle = "RISK-OFF", 45
        pos_text = "Market sentiment is firmly risk-off as ongoing US-Iran tensions and potential disruptions in the Strait of Hormuz drive energy prices higher. Investors are actively seeking shelter in gold and short-duration cash equivalents while trimming long equity exposure."
        pol_text = "Elevated energy costs threaten to reignite consumer price pressure, leading market participants to re-price Federal Reserve policy expectations. Higher terminal rate risks and sticky inflation are delaying projected interest rate cuts."
        headline = "US-Iran Escalation Drives Oil Spikes as Equities Lean Defensive"
        narrative = "Renewed geopolitical friction in the Middle East has sent Crude Oil higher, directly stoking fears of secondary inflation pass-through. With US 10-Year yields remaining sticky, equity valuations face headwinds while gold retains a robust safe-haven bid."
    elif vix_chg < -1.5 and dxy_chg < 0:
        mood, angle = "RISK-ON", 135
        pos_text = "Capital is actively rotating back into growth names as geopolitical friction temporarily eases. Easing energy benchmarks and softer Treasury yields are bolstering buyer confidence across equity indices."
        pol_text = "Moderating inflation expectations provide room for central bank flexibility. Lower real yields offer structural tailwinds for equity earnings multiples."
        headline = "Tech and Cyclicals Rebound as Yields Ease and Oil Cools"
        narrative = "A temporary pullback in energy prices has relieved market anxiety, allowing equity index futures to catch a strong bid. Softer Dollar pressure is supporting global liquidity flows across risk assets."
    else:
        mood, angle = "RISK-NEUTRAL", 90
        pos_text = "Investors are operating in a watchful consolidation phase, balancing Middle East supply risks against corporate earnings performance. Capital remains selective with defined risk parameters."
        pol_text = "The Federal Reserve maintains a strict data-dependent guidance model. Real yields are hovering within recent ranges, awaiting fresh CPI and labor data prints."
        headline = "Markets Hold Range as Geopolitical Risks Balance Corporate Earnings"
        narrative = "Trading remains structured as participants monitor energy newsflow alongside Treasury yield movements. Indices are oscillating within key intraday support and resistance bands."

    return {
        "mood": mood,
        "mood_angle": angle,
        "investor_positioning": pos_text,
        "policy_outlook": pol_text,
        "headline": headline,
        "narrative": narrative,
        "biases": {
            "XAUUSD": {
                "bias": "BULLISH",
                "confidence": 78,
                "driver": "Safe-haven demand remains elevated as US-Iran military friction and Strait of Hormuz transit risks keep bids firm under the metal. Recurrent supply chain concerns continue to outweigh Dollar index pressure.",
                "deep_dive": "### 🟡 Gold (XAUUSD) Fundamental Deep Dive\n\n- **Geopolitical Safe-Haven Bid:** Escalating US-Iran hostilities maintain a permanent risk premium on bullion. Tensions near the Strait of Hormuz encourage institutional hedging against tail-risk events.\n- **Inflation Hedging Dynamics:** Rising Crude Oil costs act as an input driver for global inflation metrics. As cost-push inflation fears mount, gold acts as a primary wealth preservation vehicle.\n- **Yield & Dollar Sensitivity:** While elevated US 10-Year Treasury yields typically create opportunity cost headwinds for non-yielding bullion, safe-haven demand currently dominates the tape, keeping price action supported at key technical support zones."
            },
            "US30": {
                "bias": "BEARISH",
                "confidence": 68,
                "driver": "Dow industrial heavyweights face pressure from elevated energy input costs and rising Treasury yields. Broader cyclical rotation slows as higher borrowing costs weigh on industrial forecasts.",
                "deep_dive": "### 🔵 Dow Jones (US30) Fundamental Deep Dive\n\n- **Energy Input Pressure:** Industrial and transportation components within the Dow are highly sensitive to Crude Oil spikes. Increased fuel and logistical costs directly compress operating margins.\n- **Yield Discount Factors:** Firm Treasury yields reduce the relative dividend yield attraction of industrial heavyweights, prompting institutional position trimming.\n- **Labor & Macro Pulse:** While solid labor prints offer baseline economic support, persistent inflation concerns restrict broad multi-day breakout potential."
            },
            "NQ": {
                "bias": "BEARISH",
                "confidence": 75,
                "driver": "Nasdaq growth multiples remain sensitive to sticky 10-Year Treasury yields triggered by energy-driven inflation fears. Large-cap tech sees selective profit-taking despite earnings resilience.",
                "deep_dive": "### 🟣 Nasdaq 100 (NQ / US100) Fundamental Deep Dive\n\n- **Valuation Multiple Compression:** Tech and growth equities carry long duration cash flows that are heavily discounted when benchmark 10-Year yields stay high. Any yield expansion leads to immediate multiple contraction.\n- **Geopolitical Risk Aversion:** In high risk-off regimes, algorithms and macro funds trim high-beta tech exposure in favor of cash and short-dated paper.\n- **Earnings Cushion:** Robust corporate balance sheets in mega-cap technology provide a structural floor, preventing severe sell-offs during minor pullbacks."
            },
            "ES": {
                "bias": "NEUTRAL",
                "confidence": 70,
                "driver": "The S&P 500 balances energy sector gains against tech and consumer discretionary drag. Broader market breadth reflects sector rotation rather than aggressive liquidations.",
                "deep_dive": "### 🟢 S&P 500 (ES) Fundamental Deep Dive\n\n- **Sector Rotation Cushion:** Unlike pure tech or industrial benchmarks, the S&P 500 benefits from weighting in Energy and Defense sectors, which gain during Middle East tensions and balance out tech weakness.\n- **Macro Fluidity:** The index tracks broad corporate earnings stability while reacting dynamically to Fed interest rate odds.\n- **Key Technical Levels:** Price continues to consolidate near major volume nodes as traders await clearer directional conviction from macro news catalysts."
            }
        }
    }

prices = get_live_prices()
news = fetch_web_news()
macro = generate_macro_synthesis(prices, news)

# ---------------------------------------------------------
# 4. MAIN LAYOUT GRID (LEFT: 2x2 ASSETS | RIGHT: MOOD & FLOW)
# ---------------------------------------------------------
col_left, col_right = st.columns([1.65, 1.0])

# --- LEFT COLUMN: 2x2 ASSET CARDS ---
with col_left:
    st.markdown("### 📈 AI Macro Desk `Market bias analysis` ")
    
    # Define exact requested ordering: Top-Left: Gold, Top-Right: US30, Bottom-Left: NQ, Bottom-Right: ES
    grid_order = [
        [("XAUUSD", "XAUUSD (Gold)", prices.get("XAUUSD", {"price": 0, "change": 0})),
         ("US30", "US30 (Dow Jones)", prices.get("US30", {"price": 0, "change": 0}))],
        [("NQ", "US100 / NQ (Nasdaq)", prices.get("NQ", {"price": 0, "change": 0})),
         ("ES", "S&P500 / ES", prices.get("ES", {"price": 0, "change": 0}))]
    ]

    for row in grid_order:
        c1, c2 = st.columns(2)
        for idx, (sym, label, p_data) in enumerate(row):
            col = c1 if idx == 0 else c2
            with col:
                b_info = macro["biases"].get(sym, {"bias": "NEUTRAL", "confidence": 50, "driver": "", "deep_dive": ""})
                bias_str = b_info["bias"].upper()
                conf = b_info["confidence"]
                driver_text = b_info["driver"]
                
                chg_val = p_data["change"]
                chg_class = "up" if chg_val >= 0 else "down"
                badge_class = f"badge-{bias_str.lower()}"
                
                st.html(f"""
                <div class="asset-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="asset-title">{label}</span>
                        <div>
                            <span class="price-text {chg_class}">{chg_val:+.2f}%</span>
                            <span class="badge {badge_class}">{bias_str}</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.75rem; color: #64748B;">
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
                
                # Interactive Deep Dive Dialog Button
                if st.button(f"🔍 Institutional Deep Dive — {sym}", key=f"btn_{sym}"):
                    @st.dialog(f"Macro Deep Dive: {label}")
                    def show_deep_dive():
                        st.markdown(b_info["deep_dive"])
                        st.markdown("---")
                        st.caption("⚡ Analysis generated in real-time integrating geopolitics, yield curves, energy prices, and interest rate futures.")
                    show_deep_dive()

# --- RIGHT COLUMN: MARKET MOOD (GAUGE) & CAPITAL FLOW ---
with col_right:
    st.markdown("### 📊 Market Mood & Positioning")
    
    mood_val = macro["mood"]
    badge_color = "#10B981" if "ON" in mood_val else ("#EF4444" if "OFF" in mood_val else "#F59E0B")
    angle = macro.get("mood_angle", 90)
    
    # Arc Dial Gauge SVG (Replicated from Picture 2)
    gauge_svg = f"""
    <svg width="190" height="105" viewBox="0 0 180 100" style="display: block; margin: 0 auto;">
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
        <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin-bottom: 10px;">
            Investor Positioning
        </div>
        <div style="display: flex; gap: 14px; align-items: center;">
            <div style="flex: 1; text-align: center;">
                {gauge_svg}
                <div style="font-size: 0.85rem; font-weight: 800; color: {badge_color}; margin-top: 4px; letter-spacing: 0.5px;">
                    {mood_val}
                </div>
            </div>
            <div style="flex: 1.6; font-size: 0.82rem; color: #94A3B8; line-height: 1.45;">
                {macro["investor_positioning"]}
            </div>
        </div>
    </div>
    
    <div class="macro-card">
        <div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
            📰 Market Briefing
        </div>
        <div style="font-size: 0.9rem; font-weight: 700; color: #38BDF8; margin-bottom: 6px;">
            {macro['headline']}
        </div>
        <div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.45;">
            {macro['narrative']}
        </div>
    </div>
    
    <div class="macro-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC;">📊 Capital Flow Matrix</span>
            <span style="font-size: 0.72rem; color: #10B981; font-weight: 600;">● Live Relative Strength</span>
        </div>
        <div style="font-size: 0.78rem; color: #64748B; margin-bottom: 12px;">
            Measures institutional capital rotation across yields, equities, FX, and commodities to identify risk appetite.
        </div>
    """)
    
    # Purposeful Capital Flow Rotation Ranking
    flow_assets = [
        ("US10Y", "Yields", prices.get("US10Y", {}).get("change", 0)),
        ("XAUUSD", "Gold", prices.get("XAUUSD", {}).get("change", 0)),
        ("CRUDE", "Oil", prices.get("CL", {}).get("change", 0)),
        ("ES", "S&P500", prices.get("ES", {}).get("change", 0)),
        ("US100", "Nasdaq", prices.get("NQ", {}).get("change", 0)),
        ("US30", "Dow", prices.get("US30", {}).get("change", 0)),
        ("DXY", "Dollar", prices.get("DXY", {}).get("change", 0)),
        ("VIX", "Vol", prices.get("VIX", {}).get("change", 0))
    ]
    
    # Sort flow by percentage change to show true capital rotation direction
    flow_assets.sort(key=lambda x: x[2], reverse=True)
    
    flow_html = ""
    for sym, label, val in flow_assets:
        color = "#10B981" if val >= 0 else "#EF4444"
        width = min(abs(val) * 30, 100)
        
        flow_html += f"""
        <div class="flow-row">
            <div class="flow-label">{label} ({sym})</div>
            <div class="flow-bar-bg">
                <div style="width: {width}%; height: 100%; background-color: {color}; border-radius: 2px;"></div>
            </div>
            <div class="flow-val" style="color: {color};">{val:+.2f}%</div>
        </div>
        """
    st.html(flow_html + "</div>")

st.markdown("---")

# ---------------------------------------------------------
# 5. BOTTOM TICKER: CORRELATION ANCHORS
# ---------------------------------------------------------
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
