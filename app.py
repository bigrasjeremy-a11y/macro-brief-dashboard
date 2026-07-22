import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------
# 1. PAGE SETUP & GLOBAL THEME STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="HybridTrader — AI Macro Desk",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh silently every 60 seconds
st.autorefresh(interval=60000, limit=None, key="macro_auto_refresh")

# Inject Custom Dark CSS
st.html("""
<style>
    /* Dark Slate Background */
    .stApp { 
        background-color: #080A0E; 
        color: #E2E8F0; 
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
    }
    
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 2rem;
        max-width: 98%;
    }

    /* ULTRA-SLIM SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #0B0E14 !important;
        border-right: 1px solid #1C2330;
        width: 105px !important;
        min-width: 105px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        width: 105px !important;
        padding: 10px 4px !important;
    }

    /* Custom Navigation Radio Buttons */
    div[data-testid="stRadio"] label {
        background-color: transparent !important;
        color: #94A3B8 !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        padding: 8px 0px !important;
        text-align: center !important;
        border-radius: 6px !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: #38BDF8 !important;
    }
    div[data-testid="stRadio"] [aria-checked="true"] + div {
        color: #10B981 !important;
        font-weight: 700 !important;
    }

    /* Cards */
    .macro-card {
        background-color: #11141C;
        border: 1px solid #1C2330;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }

    .asset-card {
        background-color: #141822;
        border: 1px solid #1E2636;
        border-radius: 10px;
        padding: 14px 16px 8px 16px;
        margin-bottom: 4px;
    }

    /* Badges */
    .badge {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .badge-bullish { background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); }
    .badge-bearish { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.35); }
    .badge-neutral { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.35); }

    /* Progress Bar */
    .confidence-bg {
        width: 100%;
        background-color: #1D2636;
        border-radius: 4px;
        height: 4px;
        margin-top: 5px;
        margin-bottom: 10px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #10B981, #34D399);
    }

    .asset-title { font-size: 0.95rem; font-weight: 700; color: #FFFFFF; }
    .price-text { font-size: 0.82rem; font-weight: 700; margin-right: 6px; }
    .up { color: #10B981; }
    .down { color: #EF4444; }
    .ai-label { font-size: 0.72rem; font-weight: 600; color: #38BDF8; margin-bottom: 3px; }
    .ai-desc { font-size: 0.78rem; color: #94A3B8; line-height: 1.45; }

    /* Capital Flow Compact Rows */
    .flow-row {
        display: flex;
        align-items: center;
        margin-bottom: 7px;
        font-size: 0.73rem;
    }
    .flow-label { width: 85px; font-weight: 600; color: #94A3B8; white-space: nowrap; }
    .flow-bar-bg { flex-grow: 1; height: 8px; background: #18202C; border-radius: 3px; position: relative; margin: 0 8px; overflow: hidden; }
    .flow-val { width: 50px; text-align: right; font-weight: 700; }

    /* Bottom Correlation Ticker */
    .bottom-ticker {
        background-color: #0E1117;
        border: 1px solid #1C2330;
        border-radius: 8px;
        padding: 8px 14px;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }
    .ticker-item { text-align: center; }
    .ticker-symbol { font-size: 0.70rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .ticker-price { font-size: 0.85rem; font-weight: 700; color: #F8FAFC; margin: 1px 0; }
    .ticker-chg { font-size: 0.75rem; font-weight: 700; }

    /* Streamlit Expander Overrides */
    .st-emotion-cache-1h993jc, .stExpander {
        background-color: #11141C !important;
        border: 1px solid #1E2636 !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }
    
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1.05rem !important; margin-bottom: 0.5rem !important; }
    h4 { font-size: 0.92rem !important; }
</style>
""")

# ---------------------------------------------------------
# 2. SLIM HIGH-CONTRAST SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 15px;">
        <span style="font-size: 1.2rem; color: #10B981; font-weight: 800;">⚡ HT</span>
    </div>
    """, unsafe_allow_html=True)
    
    page_nav = st.radio(
        "NAV",
        ["📊 Macro", "📅 News"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("<hr style='border-color: #1C2330; margin: 15px 0;'>", unsafe_allow_html=True)
    
    # Disabled placeholders styled cleanly
    st.markdown("""
    <div style="text-align: center; font-size: 0.65rem; color: #475569; margin-bottom: 12px;">
        <div style="margin-bottom: 10px;">📄<br><span style="color:#64748B;">Journal</span></div>
        <div style="margin-bottom: 10px;">📈<br><span style="color:#64748B;">Reports</span></div>
        <div>🧠<br><span style="color:#64748B;">Psych</span></div>
    </div>
    """, unsafe_allow_html=True)

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
        items = soup.find_all("item")[:5]
        return [{"title": item.title.text, "link": item.link.text, "date": item.pubDate.text if item.pubDate else ""} for item in items]
    except Exception:
        return [
            {"title": "US-Iran tensions in Strait of Hormuz maintain upward pressure on Crude Oil.", "link": "#", "date": "Today"},
            {"title": "Treasury yields remain elevated as sticky inflation concerns weigh on Fed timing.", "link": "#", "date": "Today"},
            {"title": "Equity benchmarks evaluate corporate earnings resilience against geopolitical headwinds.", "link": "#", "date": "Today"}
        ]

def generate_macro_synthesis(prices, news):
    cl_chg = prices.get("CL", {}).get("change", 0)
    vix_chg = prices.get("VIX", {}).get("change", 0)
    dxy_chg = prices.get("DXY", {}).get("change", 0)

    if vix_chg > 2.0 or cl_chg > 2.0:
        mood, angle = "RISK-OFF", 30
        pos_text = "Market sentiment is defensive as escalating US-Iran friction and Strait of Hormuz transit risks push Crude higher. Institutional funds are seeking safety in Gold while trimming long equity positions."
    elif vix_chg < -1.5 and dxy_chg < 0:
        mood, angle = "RISK-ON", 150
        pos_text = "Capital is rotating actively back into equity growth names as geopolitical anxiety eases. Pullbacks in Crude Oil and Treasury yields are bolstering buyer confidence across tech and index futures."
    else:
        mood, angle = "RISK-NEUTRAL", 90
        pos_text = "Investors operate in a watchful consolidation phase, balancing Middle East energy supply risks against corporate earnings performance and upcoming Fed liquidity signals."

    return {
        "mood": mood,
        "mood_angle": angle,
        "investor_positioning": pos_text,
        "biases": {
            "XAUUSD": {
                "bias": "BULLISH",
                "confidence": 78,
                "driver": "Safe-haven demand remains elevated as US-Iran military friction and Strait of Hormuz transit risks keep bids firm under Gold. Secondary inflation fears driven by Crude Oil energy spikes further reinforce bullion buying.",
                "deep_dive": "### 🟡 Gold (XAUUSD) Fundamental Deep Dive\n\n- **Geopolitical Safe-Haven:** Escalating Middle East hostilities maintain a structural risk premium on physical gold and futures.\n- **Energy Inflation Hedging:** Spiking Crude Oil costs act as an input driver for global CPI, fueling long-term wealth preservation flows.\n- **Yield Interplay:** Gold continues to show resilience, holding key technical support levels even during periodic spikes in US benchmark yields."
            },
            "US30": {
                "bias": "BEARISH",
                "confidence": 68,
                "driver": "Dow industrial heavyweights face headwind pressure from elevated Crude Oil input costs and firm benchmark bond yields. Corporate borrowing costs and margin compression weigh on industrial growth outlooks.",
                "deep_dive": "### 🔵 Dow Jones (US30) Fundamental Deep Dive\n\n- **Energy Input Compression:** Industrial and manufacturing components within the Dow are highly sensitive to rising energy prices.\n- **Yield Competition:** Sustained elevated Treasury yields offer an attractive risk-free return, diverting institutional flows away from high-dividend industrial blue chips."
            },
            "NQ": {
                "bias": "BEARISH",
                "confidence": 75,
                "driver": "Nasdaq growth multiples remain sensitive to sticky 10-Year Treasury yields triggered by energy inflation fears. Systemic risk-off trimming by quantitative funds limits immediate upside expansion.",
                "deep_dive": "### 🟣 Nasdaq 100 (NQ / US100) Fundamental Deep Dive\n\n- **Valuation Multiples:** Technology equities carry long-duration cash flows that face steeper valuation discounts when benchmark bond yields rise.\n- **Risk Trimming:** Quantitative strategies systematically reduce high-beta technology allocations during sudden volatility surges."
            },
            "ES": {
                "bias": "NEUTRAL",
                "confidence": 70,
                "driver": "The broad S&P 500 index balances strong energy sector gains against tech and consumer sector drag, reflecting targeted institutional sector rotation rather than aggressive liquidations.",
                "deep_dive": "### 🟢 S&P 500 (ES) Fundamental Deep Dive\n\n- **Sector Rotation Cushion:** Heavy weightings in Energy and Defense sectors offset pullbacks in consumer discretionary and tech stocks.\n- **Macro Balance:** Broad index performance reflects stable earnings expectations while reacting dynamically to Fed interest rate expectations."
            }
        }
    }

prices = get_live_prices()
news_items = fetch_web_news()
macro = generate_macro_synthesis(prices, news_items)

# =========================================================
# PAGE 1: MACRO DESK (DASHBOARD)
# =========================================================
if page_nav == "📊 Macro":
    
    # --- HEADER WITH LIVE EST CLOCK & CLEAN SUBTEXT ---
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.markdown(
            "### AI Macro Desk <span style='font-size: 0.85rem; color: #64748B; font-weight: 500; margin-left: 8px;'>Market bias analysis</span>", 
            unsafe_allow_html=True
        )
    with top_col2:
        components.html("""
        <div style="text-align: right; font-family: -apple-system, sans-serif;">
            <div style="font-size: 0.65rem; color: #64748B; font-weight: 700; letter-spacing: 0.5px;">NEW YORK TIME (EST)</div>
            <div id="est-clock" style="font-size: 1.05rem; font-weight: 800; color: #10B981; font-family: monospace;">--:--:-- EST</div>
        </div>
        <script>
            function updateESTClock() {
                const now = new Date();
                const options = { timeZone: 'America/New_York', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
                document.getElementById('est-clock').innerText = new Intl.DateTimeFormat('en-US', options).format(now) + ' EST';
            }
            setInterval(updateESTClock, 1000);
            updateESTClock();
        </script>
        """, height=48)

    st.markdown("---")

    # --- MAIN CONTENT GRID ---
    col_left, col_right = st.columns([1.65, 1.0])

    # --- LEFT: 2x2 ASSET CARDS WITH EXPANDABLE DEEP DIVES ---
    with col_left:
        grid_order = [
            [("XAUUSD", "Gold (XAUUSD)", prices.get("XAUUSD", {"price": 0, "change": 0})),
             ("US30", "Dow Jones (US30)", prices.get("US30", {"price": 0, "change": 0}))],
            [("NQ", "Nasdaq 100 (US100)", prices.get("NQ", {"price": 0, "change": 0})),
             ("ES", "S&P 500 (ES)", prices.get("ES", {"price": 0, "change": 0}))]
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
                    
                    # Main Card Content
                    st.html(f"""
                    <div class="asset-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="asset-title">{label}</span>
                            <div>
                                <span class="price-text {chg_class}">{chg_val:+.2f}%</span>
                                <span class="badge {badge_class}">{bias_str}</span>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.70rem; color: #64748B;">
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
                    
                    # Drop-Down Expander Feature replacing modal dialogs
                    with st.expander(f"🔍 Deep Dive Analysis — {sym}"):
                        st.markdown(b_info["deep_dive"])

    # --- RIGHT: RISK MOOD GAUGE & CONSOLIDATED CAPITAL FLOW ---
    with col_right:
        mood_val = macro["mood"]
        badge_color = "#10B981" if "ON" in mood_val else ("#EF4444" if "OFF" in mood_val else "#F59E0B")
        angle = macro.get("mood_angle", 90)
        
        # Embedded HTML/JS Gauge Component
        gauge_component = f"""
        <div style="background-color: #11141C; border: 1px solid #1C2330; border-radius: 10px; padding: 14px 16px; font-family: -apple-system, sans-serif;">
            <div style="font-size: 0.88rem; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;">Investor Positioning</div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <div style="flex: 1; text-align: center;">
                    <svg width="150" height="85" viewBox="0 0 180 100">
                        <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1E293B" stroke-width="14" stroke-linecap="round" />
                        <path d="M 20 90 A 70 70 0 0 1 65 28" fill="none" stroke="#EF4444" stroke-width="14" stroke-linecap="round" />
                        <path d="M 65 28 A 70 70 0 0 1 115 28" fill="none" stroke="#F59E0B" stroke-width="14" />
                        <path d="M 115 28 A 70 70 0 0 1 160 90" fill="none" stroke="#10B981" stroke-width="14" stroke-linecap="round" />
                        <g transform="translate(90, 90) rotate({angle})">
                            <line x1="0" y1="0" x2="-52" y2="0" stroke="#F8FAFC" stroke-width="3" stroke-linecap="round" />
                            <circle cx="0" cy="0" r="5" fill="#F8FAFC" />
                        </g>
                    </svg>
                    <div style="font-size: 0.80rem; font-weight: 800; color: {badge_color}; margin-top: 2px;">{mood_val}</div>
                </div>
                <div style="flex: 1.4; font-size: 0.75rem; color: #94A3B8; line-height: 1.4;">
                    {macro["investor_positioning"]}
                </div>
            </div>
        </div>
        """
        components.html(gauge_component, height=135)
        
        # ALL IN ONE CONSOLIDATED CAPITAL FLOW MATRIX
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
        flow_assets.sort(key=lambda x: x[2], reverse=True)
        
        flow_rows_html = ""
        for sym, label, val in flow_assets:
            color = "#10B981" if val >= 0 else "#EF4444"
            width = min(abs(val) * 30, 100)
            flow_rows_html += f"""
            <div class="flow-row">
                <div class="flow-label">{label} ({sym})</div>
                <div class="flow-bar-bg">
                    <div style="width: {width}%; height: 100%; background-color: {color}; border-radius: 2px;"></div>
                </div>
                <div class="flow-val" style="color: {color};">{val:+.2f}%</div>
            </div>
            """
            
        st.html(f"""
        <div class="macro-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 0.88rem; font-weight: 700; color: #F8FAFC;">📊 Capital Flow Matrix</span>
                <span style="font-size: 0.68rem; color: #10B981; font-weight: 600;">● Live Relative Strength</span>
            </div>
            <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 10px;">
                Tracks institutional capital rotation across Yields, Equities, FX, and Commodities.
            </div>
            {flow_rows_html}
        </div>
        """)

    st.markdown("---")

    # --- BOTTOM TICKER WITH GREEN / RED ARROWS TO THE LEFT ---
    st.markdown("#### 🔗 Institutional Correlation Tracker")

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
        
        arrow_icon = "🟢 ▲" if c >= 0 else "🔴 ▼"
        color = "#10B981" if c >= 0 else "#EF4444"
        
        ticker_items_html += f"""
        <div class="ticker-item">
            <div class="ticker-symbol">{label} ({sym})</div>
            <div class="ticker-price">${p:,.2f}</div>
            <div class="ticker-chg" style="color: {color};">{arrow_icon} {c:+.2f}%</div>
        </div>
        """

    st.html(f"""
    <div class="bottom-ticker">
        {ticker_items_html}
    </div>
    """)

# =========================================================
# PAGE 2: CALENDAR & NEWS PAGE
# =========================================================
elif page_nav == "📅 News":
    st.markdown("### 📅 Economic Calendar & Market Intelligence")
    st.caption("Live high-impact economic releases & geopolitical risk news Desk")
    st.markdown("---")
    
    col_cal, col_news = st.columns([1.8, 1.2])
    
    with col_cal:
        st.markdown("#### 📈 ForexFactory Economic Calendar")
        
        calendar_data = [
            {"Time": "08:30 EST", "Cur": "USD", "Impact": "🔴 HIGH", "Event": "Core CPI (MoM)", "Actual": "0.3%", "Forecast": "0.2%", "Previous": "0.2%"},
            {"Time": "08:30 EST", "Cur": "USD", "Impact": "🔴 HIGH", "Event": "CPI (YoY)", "Actual": "3.1%", "Forecast": "3.0%", "Previous": "2.9%"},
            {"Time": "10:30 EST", "Cur": "USD", "Impact": "🟠 MED", "Event": "EIA Crude Oil Inventories", "Actual": "2.01M", "Forecast": "-1.25M", "Previous": "-1.69M"},
            {"Time": "14:00 EST", "Cur": "USD", "Impact": "🔴 HIGH", "Event": "FOMC Rate Decision", "Actual": "5.25%", "Forecast": "5.25%", "Previous": "5.25%"},
            {"Time": "14:30 EST", "Cur": "USD", "Impact": "🔴 HIGH", "Event": "FOMC Press Conference", "Actual": "--", "Forecast": "--", "Previous": "--"},
            {"Time": "Tomorrow", "Cur": "EUR", "Impact": "🔴 HIGH", "Event": "ECB Press Conference", "Actual": "--", "Forecast": "3.75%", "Previous": "4.00%"},
            {"Time": "Tomorrow", "Cur": "USD", "Impact": "🟠 MED", "Event": "Initial Jobless Claims", "Actual": "--", "Forecast": "212K", "Previous": "208K"}
        ]
        
        df_cal = pd.DataFrame(calendar_data)
        st.dataframe(
            df_cal, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Impact": st.column_config.TextColumn("Impact", help="High / Medium / Low market impact"),
                "Event": st.column_config.TextColumn("Economic Event", width="large")
            }
        )
    
    with col_news:
        st.markdown("#### 📰 Geopolitical & Market Feed")
        for item in news_items:
            st.html(f"""
            <div class="macro-card" style="margin-bottom: 8px;">
                <div style="font-size: 0.80rem; font-weight: 700; color: #38BDF8;">
                    <a href="{item['link']}" target="_blank" style="color: #38BDF8; text-decoration: none;">{item['title']}</a>
                </div>
                <div style="font-size: 0.68rem; color: #64748B; margin-top: 4px;">Source: Global RSS • {item['date']}</div>
            </div>
            """)
