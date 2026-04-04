import os
import sys
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import time

# Make backend analyzer importable
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from analyzer import FlipInsightAnalyzer


# Custom CSS
def load_css():
    st.markdown("""
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg: #050608;
            --bg-soft: #0c0f14;
            --panel: #141824;
            --panel-2: #1b2130;
            --text: #eef0f6;
            --muted: #9aa4b2;
            --accent: #39ff88;
            --accent-2: #00c2ff;
            --border: rgba(255, 255, 255, 0.08);
            --shadow: 0 30px 60px rgba(0, 0, 0, 0.35);
            --radius-lg: 24px;
            --radius-md: 16px;
            --radius-sm: 12px;
        }

        .stApp {
            background: var(--bg);
            font-family: "IBM Plex Sans", sans-serif;
        }

        /* Increased font sizes for paragraphs and text */
        body, .stMarkdown, p, div, span, .stTextInput, .stSelectbox, .stMultiSelect {
            font-size: 16px !important;
        }
        
        /* Paragraph text specifically */
        p, .stMarkdown p, .element-container p {
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        
        h1 {
            font-size: 36px !important;
        }
        
        h2 {
            font-size: 30px !important;
        }
        
        h3 {
            font-size: 24px !important;
        }
        
        .stMetric label {
            font-size: 15px !important;
        }
        
        .stMetric .metric-value {
            font-size: 32px !important;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #0a0e14 0%, #06080c 100%) !important;
            border-right: 1px solid rgba(57, 255, 136, 0.2) !important;
            min-width: 280px !important;
            width: 280px !important;
        }
        
        [data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
            width: 100% !important;
            padding: 0 !important;
        }
        
        /* Remove sidebar collapse button */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* Sidebar navigation buttons */
        .stSidebar .stButton button {
            background: rgba(57, 255, 136, 0.03) !important;
            border: 1px solid rgba(57, 255, 136, 0.15) !important;
            color: var(--text) !important;
            padding: 8px 12px !important;
            margin: 3px 10px !important;
            text-align: left !important;
            font-weight: 500 !important;
            font-size: 15px !important;
            border-radius: 8px !important;
            transition: all 0.25s ease !important;
            width: calc(100% - 20px) !important;
            cursor: pointer;
        }
        
        .stSidebar .stButton button:hover {
            background: linear-gradient(135deg, rgba(57, 255, 136, 0.15), rgba(0, 194, 255, 0.15)) !important;
            color: var(--accent) !important;
            border-color: var(--accent) !important;
            transform: translateX(5px);
            box-shadow: 0 2px 8px rgba(57, 255, 136, 0.2);
        }
        
        /* Sidebar header */
        .sidebar-header {
            padding: 15px 12px 8px 12px !important;
            margin-bottom: 12px !important;
            text-align: center;
            border-bottom: 2px solid var(--accent);
            background: linear-gradient(135deg, rgba(57, 255, 136, 0.1), rgba(0, 194, 255, 0.05));
            margin: 0 10px 12px 10px !important;
            border-radius: 10px;
        }
        
        .sidebar-header .logo-icon {
            font-size: 40px;
            margin-bottom: 5px;
        }
        
        .sidebar-header .title {
            font-size: 20px;
            font-weight: 700;
            color: var(--accent);
            letter-spacing: 1px;
        }
        
        .sidebar-header .subtitle {
            font-size: 11px;
            color: var(--muted);
            margin-top: 3px;
        }
        
        /* Sidebar sections */
        .sidebar-section {
            margin-bottom: 15px !important;
            padding: 0 10px !important;
        }
        
        .sidebar-section-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 6px !important;
            margin-top: 8px !important;
            padding-left: 12px;
        }
        
        /* Data status card */
        .data-status {
            background: rgba(57, 255, 136, 0.05);
            border: 1px solid rgba(57, 255, 136, 0.2);
            border-radius: 8px;
            padding: 10px;
            margin: 8px 10px;
            text-align: center;
            font-size: 14px;
            color: var(--text);
        }
        
        /* About section */
        .about-content {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            padding: 10px;
            margin: 8px 10px;
            font-size: 12px;
            line-height: 1.5;
            color: var(--muted);
        }
        
        .feature-list {
            margin-top: 6px;
            padding-left: 18px;
        }
        
        .feature-list li {
            font-size: 11px;
            margin: 3px 0;
        }
        
        /* Main content area */
        .main .block-container {
            padding: 10px 20px 10px 25px !important;
            max-width: calc(100% - 280px) !important;
        }
        
        /* Section targets for smooth scrolling */
        .section-target {
            scroll-margin-top: 80px;
            display: block;
        }
        
        /* Background orbs */
        .bg-orb {
            position: fixed;
            width: 500px;
            height: 500px;
            border-radius: 50%;
            opacity: 0.15;
            z-index: -1;
            pointer-events: none;
        }
        
        .orb-one {
            top: -150px;
            right: -150px;
            background: radial-gradient(circle, #39ff88 0%, rgba(57, 255, 136, 0) 70%);
        }
        
        .orb-two {
            bottom: -150px;
            left: -150px;
            background: radial-gradient(circle, #00c2ff 0%, rgba(0, 194, 255, 0) 70%);
        }
        
        /* Top Bar */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            padding: 12px 20px;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            background: rgba(10, 12, 16, 0.8);
            backdrop-filter: blur(8px);
            margin-bottom: 20px;
        }
        
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .brand-mark {
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #04110a;
            font-size: 24px;
            font-weight: bold;
        }
        
        .brand h1 {
            font-size: 28px;
            letter-spacing: 0.5px;
            margin: 0;
        }
        
        .tagline {
            color: var(--muted);
            font-size: 12px;
        }
        
        .status-pill {
            font-family: monospace;
            font-size: 11px;
            padding: 4px 12px;
            border-radius: 999px;
            border: 1px solid var(--border);
            color: var(--accent);
            background: rgba(57, 255, 136, 0.08);
        }
        
        /* Hero Section */
        .hero-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .hero-copy {
            padding: 25px;
            border-radius: var(--radius-lg);
            background: linear-gradient(160deg, rgba(20, 24, 36, 0.95), rgba(10, 12, 16, 0.95));
            border: 1px solid var(--border);
        }
        
        .hero-copy h2 {
            font-size: 32px;
            margin-bottom: 12px;
        }
        
        .hero-copy p {
            color: var(--muted);
            margin-bottom: 20px;
            font-size: 16px;
            line-height: 1.6;
        }
        
        .hero-highlights {
            display: grid;
            gap: 10px;
        }
        
        .hero-highlights div {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 12px 15px;
        }
        
        .hero-highlights .label {
            color: var(--accent);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .hero-highlights .value {
            color: var(--text);
            font-size: 14px;
            margin-top: 5px;
        }
        
        /* Upload Card */
        .upload-card {
            background: var(--panel);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            padding: 25px;
        }
        
        .upload-header {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .upload-header h3 {
            font-size: 20px;
            margin: 0;
        }
        
        .upload-header p {
            color: var(--muted);
            font-size: 14px;
            margin: 5px 0 0 0;
            line-height: 1.5;
        }
        
        /* Section Titles */
        .section-title {
            margin-bottom: 25px;
            margin-top: 15px;
        }
        
        .section-title h2 {
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .section-title p {
            color: var(--muted);
            font-size: 16px;
            line-height: 1.6;
        }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: var(--panel-2);
            border-radius: var(--radius-md);
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--border);
        }
        
        /* Warning message */
        .warning-message {
            background: rgba(255, 100, 100, 0.1);
            border-left: 4px solid #ff6464;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 15px;
            color: #ff9999;
        }
        
        /* Bottle Cards */
        .bottle-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .bottle-card {
            background: linear-gradient(135deg, var(--panel), var(--panel-2));
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 18px;
            transition: transform 0.2s ease;
        }
        
        .bottle-card:hover {
            transform: translateY(-3px);
            border-color: var(--accent);
        }
        
        .bottle-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }
        
        .bottle-content {
            color: var(--muted);
            font-size: 14px;
            line-height: 1.6;
        }
        
        .bottle-stats {
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--accent-2);
        }
        
        .explanation-text {
            background: rgba(57, 255, 136, 0.05);
            border-left: 3px solid var(--accent);
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--muted);
            line-height: 1.6;
        }
        
        /* Chatbot */
        .chatbot-section {
            background: var(--panel);
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            margin-top: 15px;
            overflow: hidden;
        }
        
        .chatbot-header {
            padding: 18px 20px;
            background: linear-gradient(135deg, rgba(57, 255, 136, 0.1), rgba(0, 194, 255, 0.1));
        }
        
        .chatbot-header h3 {
            font-size: 20px;
            margin-bottom: 5px;
        }
        
        .chatbot-header p {
            color: var(--muted);
            font-size: 14px;
        }
        
        .message {
            margin-bottom: 12px;
            display: flex;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.bot {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #04110a;
        }
        
        .message.bot .message-content {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
        }
        
        .quick-questions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 10px;
            padding: 20px;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: var(--muted);
            font-size: 12px;
            padding: 20px;
            margin-top: 30px;
            border-top: 1px solid var(--border);
        }
        
        /* Streamlit overrides */
        .stFileUploader {
            background: rgba(255, 255, 255, 0.02);
            border: 1px dashed rgba(57, 255, 136, 0.5);
            border-radius: 10px;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: #04110a;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .stSelectbox > div {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
        }
        
        .stDataFrame {
            background: var(--panel-2);
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
        }
        
        /* List items */
        ul, ol {
            font-size: 15px;
            line-height: 1.6;
        }
        
        li {
            margin: 8px 0;
        }
        
        @media (max-width: 768px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }
            .bottle-grid {
                grid-template-columns: 1fr;
            }
            .main .block-container {
                max-width: 100% !important;
                padding: 10px !important;
            }
        }
    </style>
    
    <div class="bg-orb orb-one"></div>
    <div class="bg-orb orb-two"></div>
    
    <script>
        function scrollToSection(sectionId) {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start'
                });
            }
        }
        window.scrollToSection = scrollToSection;
    </script>
    """, unsafe_allow_html=True)


# Set page config
st.set_page_config(
    page_title="FlipInsight - E-commerce Intelligence & Analytics System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()

    column_mapping = {
        "productname": "product_name",
        "name": "product_name",
        "categories": "category",
        "mrp": "price",
        "discount": "discount_percentage",
        "discount%": "discount_percentage",
        "user_rating": "rating",
        "reviews": "review_count",
        "transaction_id": "order_id",
        "invoice_no": "order_id",
        "cost": "cost_price",
        "buy_price": "cost_price",
        "sell_price": "selling_price",
        "qty": "quantity",
        "purchase_date": "order_date",
        "expense": "expenditure",
        "spend": "expenditure",
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(df["price"].median())
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(df["rating"].median())

    return df


def load_dataframe(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Please upload a CSV or Excel file.")
    return normalize_columns(df)


def ensure_state():
    if "df" not in st.session_state:
        st.session_state.df = None
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = None
    if "insights" not in st.session_state:
        st.session_state.insights = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "scroll_to" not in st.session_state:
        st.session_state.scroll_to = None


def scroll_to_section(section_id):
    """Trigger scroll to section"""
    st.session_state.scroll_to = section_id


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <div class="logo-icon">📊</div>
            <div class="title">FlipInsight</div>
            <div class="subtitle">E-commerce Intelligence</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-title">📌 Navigation</div>', unsafe_allow_html=True)
        
        sections = [
            ("🏠 Dashboard", "dashboard"),
            ("📈 KPIs", "kpis"),
            ("💡 Insights", "insights"),
            ("📊 Charts", "charts"),
            ("🛍️ Products", "products"),
            ("🛒 Market Basket", "basket"),
            ("🤖 AI Model", "model"),
            ("💬 AI Assistant", "chat")
        ]
        
        for label, section_id in sections:
            # Check if this button is active
            is_active = st.session_state.page == section_id
            button_label = f"✅ {label}" if is_active else label
            
            if st.button(button_label, key=f"nav_{section_id}", use_container_width=True):
                # Check if data is loaded for non-dashboard pages
                if section_id != "dashboard" and st.session_state.df is None:
                    st.warning("⚠️ Please upload data first!")
                    st.session_state.page = "dashboard"
                else:
                    st.session_state.page = section_id
                    scroll_to_section(section_id)
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data Status Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-title">📊 Data Status</div>', unsafe_allow_html=True)
        
        if st.session_state.df is not None:
            st.markdown(f"""
            <div class="data-status">
                ✅ {len(st.session_state.df):,} rows loaded
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="data-status">
                ⏳ No data loaded<br>
                <small>Upload a file to begin</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # About Section
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-title">ℹ️ About</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="about-content">
            <strong>FlipInsight</strong> - Advanced e-commerce intelligence system
            <div class="feature-list">
                <li>📊 Real-time analytics</li>
                <li>🔍 Market basket analysis</li>
                <li>🤖 AI-powered insights</li>
                <li>💬 Interactive assistant</li>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_topbar():
    st.markdown("""
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">📊</div>
            <div>
                <h1>FlipInsight</h1>
                <p class="tagline">E-commerce Intelligence & Analytics System</p>
            </div>
        </div>
        <div class="status-pill">● ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)


def render_dashboard():
    st.markdown("""
    <div id="dashboard" class="section-target">
        <div class="section-title">
            <h2>Dashboard</h2>
            <p>Welcome to FlipInsight - Your complete e-commerce intelligence platform</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show upload section prominently
    st.markdown("""
    <div class="hero-grid">
        <div class="hero-copy">
            <h2>Turn data into insights</h2>
            <p>Upload your product data and get instant analytics</p>
            <div class="hero-highlights">
                <div>
                    <div class="label">Smart KPIs</div>
                    <div class="value">Revenue, discount, ratings analysis</div>
                </div>
                <div>
                    <div class="label">Market Basket</div>
                    <div class="value">Products frequently sold together</div>
                </div>
                <div>
                    <div class="label">AI Assist</div>
                    <div class="value">Ask questions about your data</div>
                </div>
                <div>
                    <div class="label">ML Models</div>
                    <div class="value">Rating and sales predictions</div>
                </div>
            </div>
        </div>
        <div class="upload-card">
            <div class="upload-header">
                <div>
                    <h3>📁 Upload Your Data</h3>
                    <p>Supported formats: CSV, Excel (XLSX, XLS)</p>
                    <p style="margin-top: 8px;">Required columns: Product Name, Category, Price, Discount %, Rating</p>
                    <p style="margin-top: 8px;">Optional: Transaction ID for Market Basket Analysis</p>
                </div>
            </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"], label_visibility="collapsed", key="main_uploader")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        upload_button = st.button("📊 Upload & Analyze", use_container_width=True, key="upload_btn")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    return uploaded_file, upload_button


def render_kpis(insights):
    st.markdown("""
    <div id="kpis" class="section-target">
        <div class="section-title">
            <h2>Key Performance Indicators</h2>
            <p>Quick view of your product performance metrics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📦 Total Products", f"{insights.get('total_products', 0):,}")
    with col2:
        st.metric("🏷️ Categories", f"{insights.get('total_categories', 0):,}")
    with col3:
        st.metric("💰 Avg Price", f"₹{round(insights.get('avg_price', 0)):,.0f}")
    with col4:
        st.metric("⭐ Avg Rating", f"{insights.get('avg_rating', 0):.1f} / 5")
    with col5:
        st.metric("🎯 Avg Discount", f"{round(insights.get('avg_discount', 0))}%")


def render_insights(insights):
    st.markdown("""
    <div id="insights" class="section-target">
        <div class="section-title">
            <h2>Business Insights</h2>
            <p>Actionable insights derived from your data</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🏆 Top Categories by Revenue**")
        top_rev = insights.get("top_categories_by_revenue", {})
        if top_rev:
            for cat, rev in list(top_rev.items())[:5]:
                st.write(f"• {cat}: ₹{rev:,.0f}")
        else:
            st.caption("No revenue data available")

    with col2:
        st.markdown("**⭐ Top Rated Categories**")
        top_rated = insights.get("top_categories_by_rating", {})
        if top_rated:
            for cat, rating in list(top_rated.items())[:5]:
                st.write(f"• {cat}: {rating:.1f} ⭐")
        else:
            st.caption("No rating data available")

    with col3:
        st.markdown("**📊 Product Segmentation**")
        seg = insights.get("segmentation", {})
        if seg:
            for segment, count in seg.items():
                st.write(f"• {segment}: {count} products")
        else:
            st.caption("No segmentation data available")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💰 Profit & Loss Analysis**")
        pl = insights.get("profit_loss", {})
        if pl.get("available"):
            st.write(f"Total Profit: ₹{pl['total_profit']:,.0f}")
            st.write(f"Total Loss: ₹{pl['total_loss']:,.0f}")
            st.success(f"Net Profit: **₹{pl['net_profit']:,.0f}**")
        else:
            st.caption(pl.get("note", "Profit/Loss data not available"))
    
    with col2:
        st.markdown("**📅 Avg Annual Expenditure**")
        avg = insights.get("avg_annual_expenditure", {})
        if avg.get("available"):
            st.write(f"Average: ₹{avg['average_annual_expenditure']:,.0f}")
            st.write(f"Years: {', '.join([str(y) for y in avg.get('years', [])])}")
        else:
            st.caption(avg.get("note", "Annual expenditure data not available"))
    
    st.markdown("**💡 Smart Recommendations**")
    recs = insights.get("recommendations", [])
    if recs:
        for r in recs[:6]:
            st.write(f"• {r}")
    else:
        st.caption("No recommendations available")
    
    st.markdown("**🔍 Why These Insights?**")
    exp = insights.get("insights_explanation", "")
    if exp:
        for line in exp.split("\n")[:6]:
            if line.strip():
                st.write(f"• {line}")
    else:
        st.caption("No explanation available")


def render_charts(insights):
    st.markdown("""
    <div id="charts" class="section-target">
        <div class="section-title">
            <h2>Interactive Data Visualization</h2>
            <p>Explore your data through interactive charts</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    product_list = insights.get("product_list", [])
    if not product_list:
        st.caption("No data available for charts")
        return

    df = pd.DataFrame(product_list)

    # ── Theme constants matching frontend CSS variables ──
    BG       = "#141824"
    BG_PAPER = "#0c0f14"
    TEXT     = "#eef0f6"
    MUTED    = "#9aa4b2"
    BORDER   = "rgba(255,255,255,0.08)"

    # Solid border colors (hex) and matching fill colors (rgba)
    COLORS_SOLID = [
        "#39ff88", "#00c2ff", "#ff6b9d", "#ffd166", "#a78bfa",
        "#f97316", "#06b6d4", "#84cc16", "#ec4899", "#14b8a6",
    ]
    COLORS_FILL = [
        "rgba(57,255,136,0.7)",  "rgba(0,194,255,0.7)",   "rgba(255,107,157,0.7)",
        "rgba(255,209,102,0.7)", "rgba(167,139,250,0.7)", "rgba(249,115,22,0.7)",
        "rgba(6,182,212,0.7)",   "rgba(132,204,22,0.7)",  "rgba(236,72,153,0.7)",
        "rgba(20,184,166,0.7)",
    ]

    def base_layout(title, xaxis_title="", yaxis_title=""):
        return dict(
            title=dict(text=title, font=dict(color=TEXT, size=18), x=0),
            paper_bgcolor=BG_PAPER,
            plot_bgcolor=BG,
            font=dict(family="IBM Plex Sans, sans-serif", color=MUTED, size=13),
            xaxis=dict(
                title=dict(text=xaxis_title, font=dict(color=MUTED, size=12)),
                tickfont=dict(color=MUTED, size=11),
                gridcolor=BORDER, linecolor=BORDER, zerolinecolor=BORDER,
            ),
            yaxis=dict(
                title=dict(text=yaxis_title, font=dict(color=MUTED, size=12)),
                tickfont=dict(color=MUTED, size=11),
                gridcolor=BORDER, linecolor=BORDER, zerolinecolor=BORDER,
            ),
            margin=dict(l=60, r=30, t=60, b=80),
            hoverlabel=dict(bgcolor=BG, bordercolor=BORDER, font=dict(color=TEXT, size=13)),
            showlegend=False,
        )

    chart_type = st.selectbox(
        "Select Chart Type",
        ["Top Products by Sales",
         "Category Distribution",
         "Price vs Rating Trend",
         "Discount vs Rating Trend",
         "Rating Distribution"]
    )

    # ── Chart 1: Top Products by Sales (Bar) ──
    if "Top Products by Sales" in chart_type:
        sales_data = insights.get("product_sales", [])
        if not sales_data:
            sales_data = [
                {"product_name": p["product_name"], "value": p["price"]}
                for p in product_list if isinstance(p.get("price"), (int, float))
            ]
        if sales_data:
            top    = sales_data[:20]
            labels = [d["product_name"][:22] + "…" if len(d["product_name"]) > 22 else d["product_name"] for d in top]
            values = [d.get("value", d.get("sales", 0)) for d in top]
            fills  = [COLORS_FILL[i % len(COLORS_FILL)]  for i in range(len(top))]
            lines  = [COLORS_SOLID[i % len(COLORS_SOLID)] for i in range(len(top))]

            fig = go.Figure(go.Bar(
                x=labels, y=values,
                marker=dict(color=fills, line=dict(color=lines, width=1)),
                hovertemplate="<b>%{x}</b><br>Sales: %{y:,.0f}<extra></extra>",
            ))
            fig.update_layout(**base_layout("Top Products by Sales", "Product", "Sales"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No sales data available")

    # ── Chart 2: Category Distribution (Bar) ──
    elif "Category Distribution" in chart_type:
        if "category" in df.columns:
            cat_counts = df["category"].value_counts()
            n      = len(cat_counts)
            fills  = [COLORS_FILL[i % len(COLORS_FILL)]  for i in range(n)]
            lines  = [COLORS_SOLID[i % len(COLORS_SOLID)] for i in range(n)]

            fig = go.Figure(go.Bar(
                x=cat_counts.index.tolist(),
                y=cat_counts.values.tolist(),
                marker=dict(color=fills, line=dict(color=lines, width=1)),
                hovertemplate="<b>%{x}</b><br>Products: %{y}<extra></extra>",
            ))
            fig.update_layout(**base_layout("Category Distribution", "Category", "Number of Products"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No category data available")

    # ── Chart 3: Price vs Rating Trend (Line) ──
    elif "Price vs Rating Trend" in chart_type:
        if "price" in df.columns and "rating" in df.columns:
            chart_df = df[["price", "rating"]].dropna().sort_values("price")

            fig = go.Figure(go.Scatter(
                x=chart_df["price"].tolist(),
                y=chart_df["rating"].tolist(),
                mode="lines+markers",
                line=dict(color="#39ff88", width=2),
                marker=dict(color="#39ff88", size=4),
                fill="tozeroy",
                fillcolor="rgba(57,255,136,0.12)",
                hovertemplate="Price: ₹%{x:,.0f}<br>Rating: %{y:.2f}<extra></extra>",
            ))
            fig.update_layout(**base_layout("Price vs Rating Trend", "Price (₹)", "Rating"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Price or rating data not available")

    # ── Chart 4: Discount vs Rating Trend (Line) ──
    elif "Discount vs Rating Trend" in chart_type:
        if "discount_percentage" in df.columns and "rating" in df.columns:
            chart_df = df[["discount_percentage", "rating"]].dropna().sort_values("discount_percentage")

            fig = go.Figure(go.Scatter(
                x=chart_df["discount_percentage"].tolist(),
                y=chart_df["rating"].tolist(),
                mode="lines+markers",
                line=dict(color="#00c2ff", width=2),
                marker=dict(color="#00c2ff", size=4),
                fill="tozeroy",
                fillcolor="rgba(0,194,255,0.12)",
                hovertemplate="Discount: %{x:.1f}%%<br>Rating: %{y:.2f}<extra></extra>",
            ))
            fig.update_layout(**base_layout("Discount vs Rating Trend", "Discount %", "Rating"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Discount or rating data not available")

    # ── Chart 5: Rating Distribution (Bar) ──
    elif "Rating Distribution" in chart_type:
        if "rating" in df.columns:
            rating_counts = df["rating"].value_counts().sort_index()

            fig = go.Figure(go.Bar(
                x=[str(r) for r in rating_counts.index.tolist()],
                y=rating_counts.values.tolist(),
                marker=dict(
                    color="rgba(57,255,136,0.7)",
                    line=dict(color="#39ff88", width=1),
                ),
                hovertemplate="Rating: %{x}<br>Products: %{y}<extra></extra>",
            ))
            fig.update_layout(**base_layout("Rating Distribution", "Rating", "Number of Products"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No rating data available")


def render_products(insights):
    st.markdown("""
    <div id="products" class="section-target">
        <div class="section-title">
            <h2>Products & Filters</h2>
            <p>Search, filter, and sort through your product catalog</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    product_list = insights.get("product_list", [])
    if not product_list:
        st.caption("No product list available")
        return

    df = pd.DataFrame(product_list)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search products", placeholder="Type product name...")
    with col2:
        categories = ["All"] + sorted([c for c in df["category"].dropna().unique().tolist() if c])
        category = st.selectbox("📂 Category", categories)
    with col3:
        sort_by = st.selectbox(
            "📊 Sort By",
            ["Name", "Price High", "Price Low", "Rating High", "Rating Low", 
             "Discount High", "Discount Low", "Sales High", "Sales Low"],
        )

    if search:
        df = df[df["product_name"].str.lower().str.contains(search.lower())]
    if category != "All":
        df = df[df["category"] == category]

    if "Price High" in sort_by and "price" in df.columns:
        df = df.sort_values(by="price", ascending=False)
    elif "Price Low" in sort_by and "price" in df.columns:
        df = df.sort_values(by="price", ascending=True)
    elif "Rating High" in sort_by and "rating" in df.columns:
        df = df.sort_values(by="rating", ascending=False)
    elif "Rating Low" in sort_by and "rating" in df.columns:
        df = df.sort_values(by="rating", ascending=True)
    elif "Discount High" in sort_by and "discount_percentage" in df.columns:
        df = df.sort_values(by="discount_percentage", ascending=False)
    elif "Discount Low" in sort_by and "discount_percentage" in df.columns:
        df = df.sort_values(by="discount_percentage", ascending=True)
    elif "Sales High" in sort_by and "sales" in df.columns:
        df = df.sort_values(by="sales", ascending=False)
    elif "Sales Low" in sort_by and "sales" in df.columns:
        df = df.sort_values(by="sales", ascending=True)
    else:
        df = df.sort_values(by="product_name")

    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("**🏆 Top Selling Products**")
    top_selling = insights.get("top_selling_products", [])
    if top_selling:
        for item in top_selling[:5]:
            label = "Reviews" if insights.get("sales_basis") == "review_count" else "Sales"
            st.write(f"• {item['product_name']}: {item['sales']:.0f} {label}")
    else:
        st.caption("Top sellers data unavailable")


def render_basket(insights):
    st.markdown("""
    <div id="basket" class="section-target">
        <div class="section-title">
            <h2>Market Basket Analysis</h2>
            <p>Discover product associations and customer buying patterns</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="explanation-text">
        <strong>📊 What is Market Basket Analysis?</strong><br>
        Market Basket Analysis helps identify products that are frequently purchased together. 
        By analyzing transaction data, we can discover patterns in customer buying behavior.
        This information can be used for product placement, cross-selling strategies, 
        and promotional bundling to increase sales.
    </div>
    """, unsafe_allow_html=True)

    rules = insights.get("association_rules", [])
    by_product = insights.get("association_by_product", {})
    
    if not rules and not by_product:
        st.caption("No association data available. Please ensure your data contains transaction/order IDs.")
        return
    
    if rules:
        st.markdown("### 🔗 Frequently Bought Together")
        st.markdown('<div class="bottle-grid">', unsafe_allow_html=True)
        
        for rule in rules[:8]:
            support_pct = rule["support"] * 100
            conf_a = rule["confidence_a_to_b"] * 100
            count = rule['count']
            
            summary = f"When customers purchase <strong>{rule['product_a']}</strong>, they also purchase <strong>{rule['product_b']}</strong> in {count} out of {insights.get('association_meta', {}).get('total_transactions', 0)} transactions. This happens <strong>{conf_a:.1f}%</strong> of the time."
            
            st.markdown(f"""
            <div class="bottle-card">
                <div class="bottle-title">{rule['product_a']} ↔ {rule['product_b']}</div>
                <div class="bottle-content">{summary}</div>
                <div class="bottle-stats">Support: {support_pct:.1f}% | Confidence: {conf_a:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if by_product:
        st.markdown("### 🛍️ Products Frequently Bought Together")
        st.markdown("""
        <div class="explanation-text">
            This view shows complementary products that are commonly purchased alongside each main product. 
            Use this information to create effective product bundles and cross-selling recommendations.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="bottle-grid">', unsafe_allow_html=True)
        
        for product, items in list(by_product.items())[:12]:
            if items:
                top_item = items[0]
                summary = f"When customers buy <strong>{product}</strong>, they frequently also purchase <strong>{top_item['product']}</strong>. This occurs in <strong>{top_item['count']}</strong> transactions."
                all_items = ", ".join([f"{item['product']} ({item['count']}x)" for item in items[:3]])
                
                st.markdown(f"""
                <div class="bottle-card">
                    <div class="bottle-title">{product}</div>
                    <div class="bottle-content">
                        <strong>Often bought with:</strong> {all_items}<br>
                        {summary}
                    </div>
                    <div class="bottle-stats">📦 {len(items)} complementary products identified</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_model(insights):
    st.markdown("""
    <div id="model" class="section-target">
        <div class="section-title">
            <h2>AI Model Performance</h2>
            <p>Machine learning models for rating and sales prediction</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    rating_model = insights.get("rating_model", {})
    if rating_model and "accuracy" in rating_model:
        st.info(f"""
        ### 🤖 Rating Prediction Model
        
        **Model Performance Metrics:**
        - **Accuracy (R² Score):** {rating_model['accuracy']:.1f}%
        - **RMSE:** {rating_model.get('rmse', 0):.3f}
        - **R²:** {rating_model.get('r2', 0):.3f}
        
        This model predicts product ratings based on price, discount, and category features.
        """)
    else:
        st.caption("📊 Model ready for training (requires price, discount, and rating columns in your data)")


def render_chat(analyzer):
    st.markdown("""
    <div id="chat" class="section-target">
        <div class="section-title">
            <h2>AI Sales Assistant</h2>
            <p>Ask questions about your data and get instant intelligent answers</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    quick_questions = [
        "How many products?",
        "Best performing category?",
        "Average rating?",
        "Highest revenue products?",
        "Discount insights?",
        "Price insights?",
        "Products sold together?",
        "What is market basket?"
    ]
    
    st.markdown("""
    <div class="chatbot-section">
        <div class="chatbot-header">
            <h3>🤖 Intelligent Assistant</h3>
            <p>Ask anything about your data - I'm here to help!</p>
        </div>
    """, unsafe_allow_html=True)
    
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history[-15:]:
            if msg["role"] == "user":
                st.markdown(f'<div class="message user"><div class="message-content">👤 {msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message bot"><div class="message-content">🤖 {msg["content"]}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="quick-questions-grid">', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, question in enumerate(quick_questions):
        with cols[idx % 4]:
            if st.button(question, key=f"q_{idx}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("🤔 Analyzing your question..."):
                    answer = analyzer.answer_question(question)
                st.session_state.chat_history.append({"role": "bot", "content": answer})
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


def render_footer():
    st.markdown("""
    <div class="footer">
        <strong>FlipInsight</strong> - E-commerce Intelligence System | BCA Final Year Project
    </div>
    """, unsafe_allow_html=True)


def main():
    ensure_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    render_topbar()
    
    # Show dashboard (upload section) on dashboard page
    if st.session_state.page == "dashboard":
        uploaded_file, upload_button = render_dashboard()
        
        if uploaded_file is not None and upload_button:
            try:
                with st.spinner("📊 Loading and analyzing your data..."):
                    df = load_dataframe(uploaded_file)
                    analyzer = FlipInsightAnalyzer(df)
                    insights = analyzer.perform_eda()
                    
                    st.session_state.df = df
                    st.session_state.analyzer = analyzer
                    st.session_state.insights = insights
                    st.success(f"✅ Successfully loaded {len(df):,} rows of data!")
                    st.balloons()
                    st.session_state.page = "dashboard"  # Stay on dashboard to show all content
                    st.rerun()
            except Exception as exc:
                st.error(f"❌ Error: {str(exc)}")
    
    # Render ALL content if data is loaded (for dashboard view)
    if st.session_state.insights and st.session_state.page == "dashboard":
        insights = st.session_state.insights
        render_kpis(insights)
        render_insights(insights)
        render_charts(insights)
        render_products(insights)
        render_basket(insights)
        render_model(insights)
        render_chat(st.session_state.analyzer)
    
    # Render individual pages based on selection (separate page view)
    elif st.session_state.insights and st.session_state.page != "dashboard":
        insights = st.session_state.insights
        page = st.session_state.page

        if page == "kpis":
            render_kpis(insights)
        elif page == "insights":
            render_insights(insights)
        elif page == "charts":
            render_charts(insights)
        elif page == "products":
            render_products(insights)
        elif page == "basket":
            render_basket(insights)
        elif page == "model":
            render_model(insights)
        elif page == "chat":
            render_chat(st.session_state.analyzer)
    
    render_footer()
    
    # Handle scrolling after rerun
    if st.session_state.scroll_to:
        st.markdown(f"""
        <script>
            setTimeout(function() {{
                var element = document.getElementById('{st.session_state.scroll_to}');
                if (element) {{
                    element.scrollIntoView({{ 
                        behavior: 'smooth', 
                        block: 'start'
                    }});
                }}
            }}, 200);
        </script>
        """, unsafe_allow_html=True)
        st.session_state.scroll_to = None


if __name__ == "__main__":
    if os.environ.get("STREAMLIT_RUN") != "1":
        import subprocess
        env = os.environ.copy()
        env["STREAMLIT_RUN"] = "1"
        cmd = [sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)]
        raise SystemExit(subprocess.call(cmd, env=env))
    
    main()