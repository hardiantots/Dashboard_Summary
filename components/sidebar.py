"""
sidebar.py — Komponen Sidebar & Filter Global Dashboard SIG
============================================================
Menyediakan dua fungsi utama:
  - render_sidebar(): merender kontrol filter di sidebar Streamlit.
  - filter_data()  : menerapkan filter ke ketiga DataFrame utama.

Filter bersifat global — perubahan di sini berdampak ke seluruh tab.
"""

import streamlit as st
import pandas as pd


def render_sidebar(df_revenue, df_optim, df_survey):
    """
    Merender widget filter global di sidebar dan mengembalikan nilai filter aktif.

    Parameters
    ----------
    df_revenue : pd.DataFrame  — data revenue (kolom tanggal: 'periode')
    df_optim   : pd.DataFrame  — data optimasi stok (kolom tanggal: 'week_start')
    df_survey  : pd.DataFrame  — data survei lapangan (kolom tanggal: 'year_month')

    Returns
    -------
    date_range        : tuple(date, date) — rentang waktu yang dipilih
    selected_provinsi : list[str]         — list provinsi yang dipilih
    """
    st.sidebar.title("Filter Data")

    # ── Rentang Waktu (ditentukan dinamis dari data aktual) ────────────────
    min_date = min(df_revenue["periode"].min(), df_optim["week_start"].min()).date()
    max_date = max(df_revenue["periode"].max(), df_optim["week_start"].max()).date()

    date_range = st.sidebar.date_input(
        "Rentang Waktu",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # ── Pilihan Provinsi (default: semua provinsi — gambaran nasional) ─────
    # Menggabungkan provinsi dari dataset revenue & stok secara union
    list_provinsi = sorted(
        list(
            set(df_revenue["province_desc"].dropna().unique())
            | set(df_optim["provinsi"].dropna().unique())
        )
    )
    selected_provinsi = st.sidebar.multiselect(
        "Pilih Provinsi",
        options=list_provinsi,
        default=list_provinsi,   # ← default: semua provinsi (gambaran nasional)
    )

    return date_range, selected_provinsi


def filter_data(df_revenue, df_optim, df_survey, date_range, selected_provinsi):
    """
    Menerapkan filter tanggal dan provinsi ke ketiga DataFrame.

    Catatan Filter Provinsi:
    - df_revenue menggunakan kolom 'province_desc'
    - df_optim   menggunakan kolom 'provinsi'
    - df_survey  menggunakan kolom 'provinsi'

    Parameters
    ----------
    df_revenue, df_optim, df_survey : pd.DataFrame — data mentah
    date_range        : tuple(date, date) dari st.date_input
    selected_provinsi : list[str]

    Returns
    -------
    df_rev_filtered, df_opt_filtered, df_surv_filtered : pd.DataFrame
    """
    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date   = pd.to_datetime(date_range[1])

        df_rev_filtered  = df_revenue[
            (df_revenue["periode"] >= start_date) & (df_revenue["periode"] <= end_date)
        ]
        df_opt_filtered  = df_optim[
            (df_optim["week_start"] >= start_date) & (df_optim["week_start"] <= end_date)
        ]
        df_surv_filtered = df_survey[
            (df_survey["year_month"] >= start_date) & (df_survey["year_month"] <= end_date)
        ]
    else:
        # Jika pengguna hanya memilih satu tanggal, gunakan data penuh
        df_rev_filtered  = df_revenue.copy()
        df_opt_filtered  = df_optim.copy()
        df_surv_filtered = df_survey.copy()

    if selected_provinsi:
        df_rev_filtered  = df_rev_filtered[df_rev_filtered["province_desc"].isin(selected_provinsi)]
        df_opt_filtered  = df_opt_filtered[df_opt_filtered["provinsi"].isin(selected_provinsi)]
        df_surv_filtered = df_surv_filtered[df_surv_filtered["provinsi"].isin(selected_provinsi)]

    return df_rev_filtered, df_opt_filtered, df_surv_filtered
