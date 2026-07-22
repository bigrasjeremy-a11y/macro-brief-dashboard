import streamlit as st
import pandas as pd
import datetime

# 1. PAGE CONFIGURATION & DARK THEME SETUP
st.set_page_config(
    page_title="Hybrid Macro Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme styling matching dark slate aesthetic
st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0B0E14;
            color: #E2E8F0;
        }
        /* Metric boxes */
        div[data-testid="stMetric"] {
            background-color: #161B22;
            border: 1px solid #30363D;
            padding: 15px;
            border-radius: 8px;
        }
        /* Bias cards */
        .bias-card {
            background-color: #161B22;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 5px solid #30363D;
        }
        .bullish { border-left-color: #10B981 !important; }
        .bearish { border-left-color: #EF4444 !important; }
        .neutral { border-left-color: #F59E0B !important; }
        
        .badge-bull { color: #10B981; font-weight: bold; }
        .badge-bear { color: #EF4444; font-weight: bold; }
        .badge-neu  { color: #F59E0B; font-weight: bold; }
        
        /* Headers */
        h1, h2, h3 { color: #F8FAFC !important; }
    </style>
""", unsafe_allow_html=True)

# 2. HEADER
st.title("⚡ HYBRID MACRO & FUNDAMENTAL DASHBOARD")
st.caption("Real-Time Bias Engine & Market Context Desk | XAUUSD • NQ • US30 • BTC")

# Refresh button
if st.button("🔄 Refresh Data & Sentiment"):
    st.rerun()

st.markdown("---")

# 3. MACRO TONE & MARKET REGIME
st.markdown("### 🌐 Market Regime & Macro Overview")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(label="US Dollar (DXY)", value="104.25", delta="+0.18%")
with m2:
    st.metric(label="US 10Y Yield", value="4.22%", delta="-0.04%", delta_color="inverse")
with m3:
    st.metric(label="Market Regime", value="RISK-ON", delta="Liquidity Expanding")
with m4:
    st.metric(label="Fed Rate Cut Bias", value="25-50 bps", delta="Dovish Pivot Context")

st.markdown("---")

# 4. ASSET FUNDAMENTAL BIAS ENGINE
st.markdown("### 🎯 Asset Directional Biases")

col1, col2 = st.columns(2)

assets_left = [
    {
        "symbol": "XAUUSD (Gold)",
        "bias": "BULLISH",
        "type": "bullish",
        "driver": "Lower real yields & ongoing central bank safe-haven demand.",
        "level": "Holding cleanly above key daily demand ($2,380)."
    },
    {
        "symbol": "NQ (Nasdaq 100)",
        "bias": "NEUTRAL",
        "type": "neutral",
        "driver": "Tech earnings divergence + pre-data position squaring.",
        "level": "Consolidating around session VWAP."
    }
]

assets_right = [
    {
        "symbol": "US30 (Dow Jones)",
        "bias": "BULLISH",
        "type": "bullish",
        "driver": "Sector rotation into industrial value & strong earnings tailwinds.",
        "level": "Maintaining bullish structure on H4/D1."
    },
    {
        "symbol": "BTCUSD (Bitcoin)",
        "bias": "BEARISH",
        "type": "bearish",
        "driver": "Net ETF outflows & short-term spot liquidity squeeze.",
        "level": "Testing primary support at $62,500."
    }
]

with col1:
    for item in assets_left:
        st.markdown(f"""
        <div class="bias-card {item['type']}">
            <h3 style="margin:0; font-size:1.15rem;">{item['symbol']} — <span class="badge-{item['type'][:4]}">{item['bias']}</span></h3>
            <p style="margin: 6px 0; color: #CBD5E1; font-size: 0.95rem;"><b>Primary Driver:</b> {item['driver']}</p>
            <p style="margin:0; color: #64748B; font-size: 0.85rem;"><b>Structure Note:</b> {item['level']}</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    for item in assets_right:
        st.markdown(f"""
        <div class="bias-card {item['type']}">
            <h3 style="margin:0; font-size:1.15rem;">{item['symbol']} — <span class="badge-{item['type'][:4]}">{item['bias']}</span></h3>
            <p style="margin: 6px 0; color: #CBD5E1; font-size: 0.95rem;"><b>Primary Driver:</b> {item['driver']}</p>
            <p style="margin:0; color: #64748B; font-size: 0.85rem;"><b>Structure Note:</b> {item['level']}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 5. FOREX FACTORY CALENDAR & BREAKING WIRE
c_cal, c_wire = st.columns([1, 1])

with c_cal:
    st.markdown("### 📅 Economic Calendar (Forex Factory)")
    
    cal_data = {
        "Time (EST)": ["08:30 AM", "10:00 AM", "02:00 PM"],
        "Cur.": ["USD", "USD", "USD"],
        "Event": ["Core CPI m/m", "ISM Manufacturing PMI", "FOMC Meeting Minutes"],
        "Impact": ["🔴 High", "🔴 High", "🔴 High"],
        "Forecast": ["0.3%", "48.5", "-"]
    }
    st.dataframe(pd.DataFrame(cal_data), use_container_width=True, hide_index=True)

with c_wire:
    st.markdown("### 📡 Breaking Wire (@Deitaone & InvestingLive)")
    st.info("🟢 **08:31 AM**: US CPI Prints 0.2% vs 0.3% Forecast — Dovish for USD, Bullish for Gold & NQ.")
    st.warning("🟡 **09:45 AM**: Fed's Waller notes inflation trajectory is nearing 2% target.")
    st.error("🔴 **10:05 AM**: US Crude Inventories record unexpected build.")
