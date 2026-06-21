"""
tab_models.py — Tab Peramalan & Prediksi (Machine Learning)
==============================================================
Menjalankan inferensi secara langsung dari model .pkl yang telah dilatih
(LightGBM / XGBoost, dipilih secara otomatis berdasarkan RMSE terbaik).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEATURE SETS (sesuai notebook pelatihan):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Revenue Model (Modelling_Forecast_Revenue.ipynb):
  Cat : soldto, regional, province_desc
  Lag : lag_1w_revenue, lag_4w_revenue, rolling_4w_revenue_mean/std,
        lag_1w_sellout, lag_1w_toko_aktif, lag_1w_sell_through_rate,
        rolling_4w_str_mean, lag_1w_avg_stock_toko, lag_1w_volume_sales,
        lag_1w_volume_order, lag_1w_n_toko_surveyed
  Time: month, quarter, week_of_year, month_sin/cos, week_sin/cos
  Target Y: target_revenue

Stock Model (Modelling_Optimation_Stock.ipynb):
  Cat : kode_gudang, material_code, provinsi, distributor_code
  Lag : lag_1w_actual, lag_2w_actual, lag_4w_actual,
        rolling_4w_actual_mean/std, lag_1w_sellout_gudang,
        lag_1w_stock_toko, lag_1w_vol_order_dist,
        lag_1w_fulfillment_ratio,
        lag_1w_days_of_supply  ← FITUR TURUNAN (dihitung saat inferensi)
  Time: month, quarter, week_of_year, month_sin/cos, week_sin/cos
  Target Y: actual_tonase_in

  CATATAN lag_1w_days_of_supply:
    Rumus  : lag_1w_stock_toko / (rolling_daily_sellout + 1e-5)
    rolling_daily_sellout = rolling 4-minggu total_sellout_gudang / 7.0
    Fitur ini dihitung langsung di notebook sebelum training, dan TIDAK
    ada sebagai kolom di data_for_optimizing.csv.  Tab ini menghitung
    ulang nilainya dari kolom-kolom yang ada di df_opt_filtered.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def _compute_days_of_supply(df_opt: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung ulang fitur `lag_1w_days_of_supply` dari df_opt_filtered,
    persis seperti yang dilakukan di Modelling_Optimation_Stock.ipynb.

    Rumus:
        rolling_daily_sellout = rolling 4-minggu mean(total_sellout_gudang) / 7
        lag_1w_days_of_supply = lag_1w_stock_toko / (rolling_daily_sellout + 1e-5)
        lalu di-clip ke maksimum 60 hari.

    Kolom ini TIDAK ada di data_for_optimizing.csv karena dihitung langsung
    dalam notebook modelling sebelum proses fitting.

    Parameters
    ----------
    df_opt : pd.DataFrame — data stok terfilter, diurutkan berdasarkan week_start

    Returns
    -------
    df_opt : pd.DataFrame — salinan dengan kolom `lag_1w_days_of_supply` ditambahkan
    """
    df = df_opt.sort_values(["kode_gudang", "material_code", "week_start"]).copy()

    # rolling_daily_sellout: rata-rata serapan harian (shift 1 agar tidak bocor)
    df["_rolling_daily_sellout"] = (
        df.groupby(["kode_gudang", "material_code"])["total_sellout_gudang"]
        .transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
        / 7.0
    )

    # lag_1w_days_of_supply: sisa hari ketahanan stok minggu lalu
    df["lag_1w_days_of_supply"] = (
        df["lag_1w_stock_toko"] / (df["_rolling_daily_sellout"].fillna(0) + 1e-5)
    ).clip(upper=60)

    df.drop(columns=["_rolling_daily_sellout"], inplace=True)
    return df


def _safe_encode(X: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    """
    Terapkan LabelEncoder per kolom kategorik dengan fallback ke kelas pertama
    jika nilai tidak dikenali (unseen label — sesuai pola notebook pelatihan).
    """
    X = X.copy()
    for col, encoder in encoders.items():
        if col in X.columns:
            known_classes = list(encoder.classes_)
            X[col] = X[col].astype(str).apply(
                lambda v: v if v in known_classes else known_classes[0]
            )
            X[col] = encoder.transform(X[col])
    return X


def render_tab_models(
    df_rev_filtered, df_opt_filtered, rev_model, stock_model, rev_enc, stock_enc
):
    st.header("Sistem Peramalan & Prediksi (Machine Learning)")
    st.markdown(
        "Inferensi langsung dari model **LightGBM / XGBoost** yang telah dilatih. "
        "Pilih entitas (distributor atau gudang), lalu dashboard akan mengambil kondisi "
        "historis terbaru dan menghasilkan prediksi real-time beserta analisis driver."
    )

    col1, col2 = st.columns(2)

    # ─────────────────────────────────────────────────────────────────────────
    # 🔮 SIMULASI REVENUE
    # ─────────────────────────────────────────────────────────────────────────
    with col1:
        st.subheader("🔮 Simulasi Revenue")
        if df_rev_filtered.empty:
            st.warning("Data revenue kosong untuk filter saat ini.")
        else:
            selected_dist = st.selectbox(
                "Pilih Distributor (Sold-To)", df_rev_filtered["soldto"].unique()
            )
            # Ambil baris terbaru (data aktual paling mutakhir) untuk distributor terpilih
            sample_data = (
                df_rev_filtered[df_rev_filtered["soldto"] == selected_dist]
                .sort_values("periode")
                .iloc[-1:]
            )

            # Ambil daftar fitur dari model (LightGBM: feature_name_, sklearn: feature_names_in_)
            features = getattr(
                rev_model, "feature_name_",
                getattr(rev_model, "feature_names_in_", None)
            )

            if features is None:
                st.warning("Model revenue tidak memiliki metadata fitur. Pastikan model dilatih ulang.")
            else:
                # Reindex ke feature set model (kolom yang tidak ada diisi 0)
                X = sample_data.reindex(columns=features, fill_value=0).copy()
                try:
                    X = _safe_encode(X, rev_enc)
                    prediction = rev_model.predict(X)[0]
                    aktual      = sample_data["target_revenue"].values[0]
                    delta_pct   = ((prediction - aktual) / aktual * 100) if aktual != 0 else 0

                    st.metric(
                        "Prediksi Target Revenue",
                        f"Rp {prediction:,.0f}",
                        f"{delta_pct:+.2f}% vs Aktual Terakhir",
                    )
                    st.caption(
                        f"Aktual Revenue Baris Terpilih (Baseline): **Rp {aktual:,.0f}**  \n"
                        f"Periode: `{sample_data['periode'].values[0]}`"
                    )

                    # Feature Importance — Top 10 driver prediksi
                    importances = getattr(rev_model, "feature_importances_", None)
                    if importances is not None:
                        df_imp = (
                            pd.DataFrame({"Fitur": features, "Kepentingan": importances})
                            .sort_values("Kepentingan", ascending=False)
                            .head(10)
                        )
                        fig_imp = px.bar(
                            df_imp, x="Kepentingan", y="Fitur", orientation="h",
                            title="Top 10 Driver Pendorong Prediksi Revenue",
                            template="plotly_white",
                            color_discrete_sequence=["#3498db"],
                        )
                        fig_imp.update_layout(yaxis={"categoryorder": "total ascending"}, height=350)
                        st.plotly_chart(fig_imp, use_container_width=True)
                        st.info(
                            "💡 **Insight Driver:** Fitur dengan kepentingan tertinggi adalah faktor "
                            "yang paling dominan dalam menentukan prediksi revenue distributor ini. "
                            "Lag revenue minggu sebelumnya biasanya menjadi prediktor terkuat "
                            "(autoregressive signal)."
                        )

                except Exception as e:
                    st.error(f"Error prediksi revenue: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 🚚 SIMULASI KEBUTUHAN STOK
    # ─────────────────────────────────────────────────────────────────────────
    with col2:
        st.subheader("🚚 Simulasi Kebutuhan Stok")
        if df_opt_filtered.empty:
            st.warning("Data stok kosong untuk filter saat ini.")
        else:
            selected_wh = st.selectbox(
                "Pilih Gudang (Kode Gudang)", df_opt_filtered["kode_gudang"].unique()
            )

            # Hitung ulang lag_1w_days_of_supply untuk seluruh df_opt_filtered
            # (perlu data semua gudang agar rolling window per grup bisa dihitung dengan benar)
            df_opt_enriched = _compute_days_of_supply(df_opt_filtered)

            # Ambil baris terbaru gudang terpilih dari data yang sudah di-enrich
            sample_data = (
                df_opt_enriched[df_opt_enriched["kode_gudang"] == selected_wh]
                .sort_values("week_start")
                .iloc[-1:]
            )

            features = getattr(
                stock_model, "feature_name_",
                getattr(stock_model, "feature_names_in_", None)
            )

            if features is None:
                st.warning("Model stok tidak memiliki metadata fitur. Pastikan model dilatih ulang.")
            else:
                # Reindex ke feature set model; lag_1w_days_of_supply sudah ada di sample_data
                X = sample_data.reindex(columns=features, fill_value=0).copy()
                try:
                    X = _safe_encode(X, stock_enc)
                    prediction = stock_model.predict(X)[0]
                    aktual      = sample_data["actual_tonase_in"].values[0]
                    delta_pct   = ((prediction - aktual) / aktual * 100) if aktual != 0 else 0

                    st.metric(
                        "Prediksi Kebutuhan Suplai (Tonase In)",
                        f"{prediction:,.2f} TON",
                        f"{delta_pct:+.2f}% vs Aktual Terakhir",
                    )
                    st.caption(
                        f"Aktual Tonase In (Baseline): **{aktual:,.2f} TON**  \n"
                        f"Minggu: `{sample_data['week_start'].values[0]}`  |  "
                        f"Days of Supply: **{sample_data['lag_1w_days_of_supply'].values[0]:.1f} hari**"
                    )

                    # Feature Importance — Top 10 driver prediksi
                    importances = getattr(stock_model, "feature_importances_", None)
                    if importances is not None:
                        df_imp = (
                            pd.DataFrame({"Fitur": features, "Kepentingan": importances})
                            .sort_values("Kepentingan", ascending=False)
                            .head(10)
                        )
                        fig_imp = px.bar(
                            df_imp, x="Kepentingan", y="Fitur", orientation="h",
                            title="Top 10 Driver Kebutuhan Stok Gudang",
                            template="plotly_white",
                            color_discrete_sequence=["#e67e22"],
                        )
                        fig_imp.update_layout(yaxis={"categoryorder": "total ascending"}, height=350)
                        st.plotly_chart(fig_imp, use_container_width=True)
                        st.info(
                            "💡 **Insight Driver:** `lag_1w_days_of_supply` (sisa hari ketahanan stok) "
                            "merupakan fitur buatan (*engineered feature*) yang menggabungkan informasi "
                            "stok toko dan kecepatan jual harian — biasanya menjadi salah satu prediktor "
                            "terkuat untuk kebutuhan restocking gudang."
                        )

                except Exception as e:
                    st.error(f"Error prediksi stok: {e}")
