"""
data_loader.py — Modul Pemuatan Data & Model Dashboard SIG
===========================================================
Bertanggung jawab atas loading seluruh dataset dan model ML yang
dibutuhkan dashboard. Semua fungsi menggunakan Streamlit cache untuk
menghindari reload berulang saat interaksi filter.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASAL-USUL DATA (Pipeline Lengkap):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. data_for_forecast_revenue.csv
   └─ Sumber  : Proses_Agregasi_Data_Forecasting.ipynb (Bagian 2)
   └─ Input   : table_sell_in_new.csv, table_sell_out_new.csv,
                table_CA_new.csv, table_survey_new.csv
   └─ Granularitas: Distributor (soldto) × Minggu
   └─ Target Y: target_revenue (total sell-in revenue per distributor/minggu)

2. data_for_optimizing.csv
   └─ Sumber  : Proses_Agregasi_Data_Forecasting.ipynb (Bagian 3)
   └─ Input   : sama seperti di atas (dengan skeleton grid gudang × material)
   └─ Granularitas: Gudang (kode_gudang) × Material Code × Minggu
   └─ Target Y: actual_tonase_in (volume masuk ke gudang per material/minggu)
   └─ Fitur tambahan: safety_stock_est, reorder_point_est, utilisasi_vs_ca

3. dim_survey.csv
   └─ Sumber  : Pipeline ETL terpisah (For_Dashboard/) — agregasi survey
                lapangan yang sudah diproses ke level salesman × provinsi × bulan.
   └─ Kolom kunci: brand, salesman, provinsi, avg_fill_rate, stockout_rate,
                   total_volume_sales, avg_stock_utilization, n_visits
   └─ Catatan : Dataset ini menggunakan skema yang berbeda dari
                table_survey_new.csv (yang digunakan di notebook agregasi).
                dim_survey.csv adalah agregat final untuk visualisasi lapangan.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASAL-USUL MODEL (.pkl):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- best_revenue_model.pkl  + encoders_revenue.pkl
  └─ Sumber: Modelling_Forecast_Revenue.ipynb
  └─ Algoritma: XGBoost / LightGBM Regressor
  └─ Target: target_revenue

- best_stock_model.pkl + encoders_stock.pkl
  └─ Sumber: Modelling_Optimation_Stock.ipynb
  └─ Algoritma: XGBoost / LightGBM Regressor
  └─ Target: actual_tonase_in
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import pandas as pd
import os
import joblib


@st.cache_data
def load_data():
    """
    Memuat tiga dataset utama dashboard dari direktori dataset/.

    Returns
    -------
    df_revenue : pd.DataFrame
        Dataset forecasting revenue level distributor × minggu.
        Kolom tanggal: 'periode' (datetime, weekly anchor).

    df_optim : pd.DataFrame
        Dataset optimasi stok level gudang × material × minggu.
        Kolom tanggal: 'week_start' (datetime).
        Fitur turunan: reorder_point_est, safety_stock_est, utilisasi_vs_ca.

    df_survey : pd.DataFrame
        Data intelijen lapangan level salesman × provinsi × bulan.
        Kolom tanggal: 'year_month' (datetime, dikonversi ke tanggal awal bulan).
        Sumber: Pipeline ETL dim_survey — skema berbeda dari table_survey_new.csv.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")

    path_revenue = os.path.join(dataset_dir, "data_for_forecast_revenue.csv")
    path_optim   = os.path.join(dataset_dir, "data_for_optimizing.csv")
    # dim_survey.csv: agregat lapangan (ETL terpisah) — lihat docstring modul untuk detail
    path_survey  = os.path.join(dataset_dir, "dim_survey.csv")

    # ── Revenue Forecasting (distributor × minggu) ─────────────────────────
    df_revenue = pd.read_csv(path_revenue)
    df_revenue["periode"] = pd.to_datetime(df_revenue["periode"])

    # ── Optimasi Stok (gudang × material × minggu) ─────────────────────────
    df_optim = pd.read_csv(path_optim)
    df_optim["week_start"] = pd.to_datetime(df_optim["week_start"])

    # ── Survei Lapangan (salesman × provinsi × bulan) ──────────────────────
    # year_month di CSV berformat 'YYYY-MM', dikonversi ke tanggal awal bulan
    df_survey = pd.read_csv(path_survey)
    df_survey["year_month"] = pd.to_datetime(df_survey["year_month"] + "-01")

    return df_revenue, df_optim, df_survey


@st.cache_resource
def load_models():
    """
    Memuat model ML yang telah di-training dan encoder kategorikalnya.

    Returns
    -------
    rev_model   : Estimator sklearn/XGBoost/LightGBM untuk prediksi revenue.
    stock_model : Estimator sklearn/XGBoost/LightGBM untuk prediksi tonase stok.
    rev_enc     : dict — encoder per kolom kategorik model revenue.
    stock_enc   : dict — encoder per kolom kategorik model stok.

    Notes
    -----
    Menggunakan @st.cache_resource (bukan @st.cache_data) karena objek model
    tidak dapat di-serialize ulang setiap sesi — cukup dimuat sekali per proses.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")

    rev_model   = joblib.load(os.path.join(models_dir, "best_revenue_model.pkl"))
    stock_model = joblib.load(os.path.join(models_dir, "best_stock_model.pkl"))

    rev_enc   = joblib.load(os.path.join(models_dir, "encoders_revenue.pkl"))
    stock_enc = joblib.load(os.path.join(models_dir, "encoders_stock.pkl"))

    return rev_model, stock_model, rev_enc, stock_enc
