import streamlit as st

st.set_page_config(
    page_title="CryptoAdvisor Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# Custom CSS - dark trading theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'Inter', sans-serif; }
code, .mono { font-family: 'JetBrains Mono', monospace; }

/* Dark background */
.stApp { background-color: #0d0f14; }
[data-testid="stSidebar"] { background-color: #111318 !important; border-right: 1px solid #1e2130; }

/* Remove default streamlit styling */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebarNav"] {display: none;}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #151821 0%, #1a1f2e 100%);
    border: 1px solid #252a3a;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 6px 0;
}
.metric-label { color: #6b7280; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
.metric-value { color: #f1f5f9; font-size: 26px; font-weight: 700; margin: 4px 0; font-family: 'JetBrains Mono', monospace; }
.metric-change-pos { color: #10b981; font-size: 13px; font-weight: 600; }
.metric-change-neg { color: #ef4444; font-size: 13px; font-weight: 600; }

/* Signal badges */
.signal-buy {
    background: linear-gradient(135deg, #065f46, #047857);
    border: 1px solid #10b981;
    color: #6ee7b7;
    padding: 6px 16px; border-radius: 20px;
    font-weight: 700; font-size: 13px; letter-spacing: 1px;
    display: inline-block;
}
.signal-sell {
    background: linear-gradient(135deg, #7f1d1d, #991b1b);
    border: 1px solid #ef4444;
    color: #fca5a5;
    padding: 6px 16px; border-radius: 20px;
    font-weight: 700; font-size: 13px; letter-spacing: 1px;
    display: inline-block;
}
.signal-neutral {
    background: linear-gradient(135deg, #1e2130, #252a3a);
    border: 1px solid #374151;
    color: #9ca3af;
    padding: 6px 16px; border-radius: 20px;
    font-weight: 700; font-size: 13px; letter-spacing: 1px;
    display: inline-block;
}

/* Indicator row */
.indicator-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 0; border-bottom: 1px solid #1e2130;
}
.indicator-name { color: #9ca3af; font-size: 13px; }
.indicator-val { color: #f1f5f9; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500; }

/* Section headers */
.section-header {
    color: #6366f1; font-size: 11px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 1px solid #1e2130;
}

/* Alert boxes */
.alert-buy {
    background: rgba(16, 185, 129, 0.08);
    border-left: 3px solid #10b981;
    border-radius: 6px; padding: 14px 18px; margin: 10px 0;
}
.alert-sell {
    background: rgba(239, 68, 68, 0.08);
    border-left: 3px solid #ef4444;
    border-radius: 6px; padding: 14px 18px; margin: 10px 0;
}
.alert-neutral {
    background: rgba(99, 102, 241, 0.08);
    border-left: 3px solid #6366f1;
    border-radius: 6px; padding: 14px 18px; margin: 10px 0;
}

/* Stbutton override */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 10px 24px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #4338ca, #4f46e5) !important;
    box-shadow: 0 0 20px rgba(99,102,241,0.3) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] { color: #6b7280 !important; }
.stTabs [aria-selected="true"] { color: #6366f1 !important; border-bottom-color: #6366f1 !important; }

/* Select boxes */
.stSelectbox > div > div { background: #151821 !important; border-color: #252a3a !important; color: #f1f5f9 !important; }

/* Sidebar text */
.css-1d391kg, [data-testid="stSidebar"] * { color: #d1d5db; }

/* Price ticker */
.price-ticker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 42px; font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

from views.dashboard import show_dashboard
from views.signals import show_signals
from views.analysis import show_analysis
from views.settings import show_settings

# Sidebar navigation
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 24px 0;">
        <div style="font-size:22px; font-weight:800; color:#818cf8;">⚡ CryptoAdvisor</div>
        <div style="font-size:11px; color:#4b5563; letter-spacing:2px; margin-top:4px;">PRO TRADING SUITE</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Nawigacja",
        ["📊  Dashboard", "🎯  Sygnały", "🔬  Analiza", "⚙️  Ustawienia"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px; color:#374151; padding: 10px 0;">
        <div style="color:#10b981; font-weight:600; margin-bottom:6px;">● POŁĄCZONO z Binance</div>
        Dane aktualizowane co 30s
    </div>
    """, unsafe_allow_html=True)

# Route pages
if "Dashboard" in page:
    show_dashboard()
elif "Sygnały" in page:
    show_signals()
elif "Analiza" in page:
    show_analysis()
elif "Ustawienia" in page:
    show_settings()
