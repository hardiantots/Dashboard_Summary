import streamlit as st

# Set Konfigurasi Halaman harus menjadi perintah st pertama
st.set_page_config(
    page_title="Dashboard Interaktif SIG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data_loader import load_data, load_models
from utils.styles import apply_custom_css
from components.sidebar import render_sidebar, filter_data
from components.kpi_cards import render_kpi_cards
from tabs.tab_revenue import render_tab_revenue
from tabs.tab_stock import render_tab_stock
from tabs.tab_survey import render_tab_survey
from tabs.tab_models import render_tab_models

# Terapkan Custom CSS
apply_custom_css()

# Muat Data
try:
    df_revenue, df_optim, df_survey = load_data()
    rev_model, stock_model, rev_enc, stock_enc = load_models()
except Exception as e:
    st.error(f"Gagal memuat data atau model: {e}")
    st.stop()

# Sidebar & Filtering
date_range, selected_provinsi = render_sidebar(df_revenue, df_optim, df_survey)
df_rev_filtered, df_opt_filtered, df_surv_filtered = filter_data(
    df_revenue, df_optim, df_survey, date_range, selected_provinsi
)

if df_rev_filtered.empty or df_opt_filtered.empty:
    st.warning(
        "⚠️ Tidak ada data yang cocok dengan kombinasi filter saat ini. Silakan sesuaikan filter di sidebar."
    )
    st.stop()

# Konfigurasi LLM API Key (OpenRouter)
api_key = None
try:
    api_key = st.secrets.get("OPENROUTER_API_KEY")
except (FileNotFoundError, KeyError):
    pass

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Status Sistem AI")

if not api_key or api_key == "sk-or-v1-API-KEY-ANDA-DI-SINI":
    st.sidebar.error("🔴 **API Disconnected**\n\nAI Engine tidak aktif.")
    api_key_input = st.sidebar.text_input(
        "🔑 Masukkan OpenRouter API Key", type="password"
    )
    if api_key_input:
        api_key = api_key_input
        st.rerun()  # Refresh agar status langsung berubah
else:
    st.sidebar.success(
        "🟢 **API Connected**\n\nModel: `NVIDIA: Nemotron 3 Super (free)`"
    )

# Header Dashboard
st.title("Proyek Intelijen Bisnis Sales Semen")
st.subheader("Dashboard Interaktif Sales & Supply Chain (Jan–Des 2026)")

# Render KPI Cards
render_kpi_cards(df_rev_filtered, df_opt_filtered, df_surv_filtered)

st.markdown("---")

# Render Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Analisis Komersial & Revenue",
        "📦 Manajemen & Optimasi Stok",
        "📋 Intelijen Operasional Lapangan",
        "🔮 Peramalan & Optimasi (ML)",
    ]
)

with tab1:
    render_tab_revenue(df_rev_filtered, df_surv_filtered, api_key)

with tab2:
    render_tab_stock(df_opt_filtered, api_key)

with tab3:
    render_tab_survey(df_surv_filtered)

with tab4:
    render_tab_models(
        df_rev_filtered, df_opt_filtered, rev_model, stock_model, rev_enc, stock_enc
    )
