import streamlit as st
import pandas as pd


def render_sidebar(df_revenue, df_optim, df_survey):
    st.sidebar.title("Filter Data")

    # Dictionary Mapping untuk Material Code (Asumsi Bisnis Semen)
    MAT_DICT = {
        "MAT001": "Semen Portland Tipe I",
        "MAT002": "Semen PCC Premium",
        "MAT003": "Semen Tecton Khusus",
        "MAT004": "Semen Portland Komposit",
    }

    # Ekstraksi rentang waktu dinamis
    min_date = min(df_revenue["periode"].min(), df_optim["week_start"].min()).date()
    max_date = max(df_revenue["periode"].max(), df_optim["week_start"].max()).date()

    date_range = st.sidebar.date_input(
        "Rentang Waktu",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Ekstraksi list Provinsi unik
    list_provinsi = sorted(
        list(
            set(df_revenue["province_desc"].dropna().unique())
            | set(df_optim["provinsi"].dropna().unique())
        )
    )
    selected_provinsi = st.sidebar.multiselect(
        "Pilih Provinsi",
        options=list_provinsi,
        default=list_provinsi[:3] if len(list_provinsi) > 3 else list_provinsi,
    )

    return date_range, selected_provinsi

def filter_data(
    df_revenue, df_optim, df_survey, date_range, selected_provinsi
):
    if len(date_range) == 2:
        start_date, end_date = date_range
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        df_rev_filtered = df_revenue[
            (df_revenue["periode"] >= start_date) & (df_revenue["periode"] <= end_date)
        ]
        df_opt_filtered = df_optim[
            (df_optim["week_start"] >= start_date)
            & (df_optim["week_start"] <= end_date)
        ]
        df_surv_filtered = df_survey[
            (df_survey["year_month"] >= start_date)
            & (df_survey["year_month"] <= end_date)
        ]
    else:
        df_rev_filtered = df_revenue.copy()
        df_opt_filtered = df_optim.copy()
        df_surv_filtered = df_survey.copy()

    if selected_provinsi:
        df_rev_filtered = df_rev_filtered[
            df_rev_filtered["province_desc"].isin(selected_provinsi)
        ]
        df_opt_filtered = df_opt_filtered[
            df_opt_filtered["provinsi"].isin(selected_provinsi)
        ]
        df_surv_filtered = df_surv_filtered[
            df_surv_filtered["provinsi"].isin(selected_provinsi)
        ]

    return df_rev_filtered, df_opt_filtered, df_surv_filtered
