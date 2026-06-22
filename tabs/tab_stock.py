"""
tab_stock.py — Tab Manajemen & Optimasi Stok
=============================================
Menyajikan analisis supply-demand berbasis Coverage Ratio (SI/SO),
PuLP Prescriptive Solver untuk alokasi logistik, serta visualisasi
utilisasi gudang dan Reorder Point (ROP).

Definisi Coverage Ratio yang digunakan secara konsisten:
    Coverage Ratio = Sell-In / Sell-Out  (SI/SO)
    < COVERAGE_LOWER  → Defisit Pasokan  (pasar menyerap lebih cepat dari kiriman)
    > COVERAGE_UPPER  → Surplus Pasokan  (akumulasi stok, relokasi / promosi diperlukan)
    Antara kedua batas → Seimbang (Balanced)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pulp
from utils.llm_engine import generate_dispatch_memo
from config import MAT_DICT, COVERAGE_LOWER, COVERAGE_UPPER, COVERAGE_COLOR_MAP


def render_tab_stock(df_opt_filtered, api_key):
    st.header("Keseimbangan Pasokan & Stok")

    st.markdown("---")
    st.markdown("### 🎛️ Filter Khusus Modul Stok")

    # ── Filter Material Code ───────────────────────────────────────────────
    # MAT_DICT di-import dari config.py agar konsisten dengan modul lain
    list_material_raw     = sorted(list(df_opt_filtered["material_code"].dropna().unique()))
    list_material_display = [f"{m} ({MAT_DICT.get(m, 'Produk Lainnya')})" for m in list_material_raw]

    selected_material_display = st.multiselect(
        "Pilih Material Code untuk Analisis Stok di bawah ini:",
        options=list_material_display,
        default=list_material_display,
    )

    # Kembalikan ke kode material asli untuk filtering
    selected_material = [m.split(" ")[0] for m in selected_material_display]

    df_opt_tab2 = df_opt_filtered.copy()
    if selected_material:
        df_opt_tab2 = df_opt_tab2[df_opt_tab2["material_code"].isin(selected_material)]

    if not df_opt_tab2.empty:

        # ─────────────────────────────────────────────────────────────────
        # ⚡ PRESCRIPTIVE SOLVER — PuLP Alokasi Logistik
        # ─────────────────────────────────────────────────────────────────
        st.markdown("### ⚡ Prescriptive Solver (PuLP Alokasi Logistik)")

        with st.expander("ℹ️ Catatan Metodologi Solver", expanded=False):
            st.info(
                "**Tingkat Agregasi:** Solver ini beroperasi pada level **gudang** "
                "(rata-rata `reorder_point_est` dan `target_tonase_ca` per `kode_gudang`, "
                "tanpa pemisahan per material code). Ini adalah simplifikasi yang valid untuk "
                "demonstrasi prescriptive analytics tingkat jaringan distribusi.  \n\n"
                "**Untuk implementasi operasional,** alokasi per-SKU memerlukan granularitas "
                "`kode_gudang × material_code` yang lebih dalam, beserta constraint tambahan "
                "seperti minimum order quantity (MOQ) dan jadwal pengiriman aktual."
            )

        if st.button("Jalankan Solver Alokasi Logistik (PuLP)", type="primary"):
            with st.spinner("Menjalankan Linear Programming..."):
                try:
                    # Agregasi rata-rata per gudang (ROP & kapasitas CA)
                    df_solve = (
                        df_opt_tab2
                        .groupby("kode_gudang")[["reorder_point_est", "target_tonase_ca"]]
                        .mean()
                        .reset_index()
                        .dropna()
                    )

                    # Batas suplai silo pabrik pusat (90% dari total kapasitas jaringan)
                    factory_limit_national = df_solve["target_tonase_ca"].sum() * 0.90

                    # ── Deklarasi LP Problem ───────────────────────────────────
                    prob = pulp.LpProblem("Logistics_Allocation_Optimization", pulp.LpMaximize)

                    # Decision Variables: alokasi tonase ke setiap gudang (≥ 0)
                    alloc_vars = pulp.LpVariable.dicts(
                        "Alloc", df_solve["kode_gudang"], lowBound=0, cat="Continuous"
                    )

                    # Objective Function: maksimalkan total pemenuhan pasokan
                    prob += pulp.lpSum([alloc_vars[g] for g in df_solve["kode_gudang"]])

                    # Constraint 1 — Batas suplai nasional dari silo pabrik pusat (90%)
                    prob += (
                        pulp.lpSum([alloc_vars[g] for g in df_solve["kode_gudang"]])
                        <= factory_limit_national
                    )

                    # Constraint 2 & 3 — Per gudang: alokasi ≤ ROP (ML) & ≤ kapasitas CA
                    for _, row in df_solve.iterrows():
                        g = row["kode_gudang"]
                        prob += alloc_vars[g] <= row["reorder_point_est"]
                        prob += alloc_vars[g] <= row["target_tonase_ca"]

                    prob.solve(pulp.PULP_CBC_CMD(msg=0))  # msg=0 → suppress solver log

                    # ── Ekstraksi Hasil ────────────────────────────────────────
                    results = []
                    for _, row in df_solve.iterrows():
                        g = row["kode_gudang"]
                        alokasi  = alloc_vars[g].varValue or 0.0
                        kebutuhan = row["reorder_point_est"]
                        kapasitas = row["target_tonase_ca"]
                        pemenuhan_pct = (alokasi / kebutuhan * 100) if kebutuhan > 0 else 0.0
                        results.append({
                            "Gudang":               g,
                            "Kapasitas Maks (TON)": round(kapasitas, 2),
                            "Kebutuhan ML (TON)":   round(kebutuhan, 2),
                            "Alokasi (TON)":        round(alokasi, 2),
                            "Pemenuhan (%)":        round(pemenuhan_pct, 1),
                        })

                    df_pulp = pd.DataFrame(results)

                    col1, col2 = st.columns([2, 1])
                    with col1:
                        status_label = pulp.LpStatus[prob.status]
                        total_alloc  = pulp.value(prob.objective) or 0.0
                        st.success(
                            f"Status Solver: **{status_label}** | "
                            f"Total Alokasi: **{total_alloc:,.0f} TON**"
                        )
                        st.dataframe(df_pulp, use_container_width=True, hide_index=True)
                    with col2:
                        st.info(
                            f"**Batas Suplai Silo Pusat (90%):**  \n"
                            f"{factory_limit_national:,.0f} TON"
                        )

                    # ── AI Dispatch Memo ───────────────────────────────────────
                    st.markdown("#### 🤖 AI Dispatch Memo (Surat Instruksi Rebalancing)")
                    with st.spinner("Menyintesis Surat Instruksi Kepala Gudang via OpenRouter..."):
                        memo = generate_dispatch_memo(df_pulp, api_key)
                        st.warning(memo)

                except Exception as e:
                    st.error(f"Gagal menjalankan Solver PuLP: {e}")

        # ─────────────────────────────────────────────────────────────────
        # 📊 ANALISIS SELL-IN vs SELL-OUT & COVERAGE RATIO PER PROVINSI
        # ─────────────────────────────────────────────────────────────────
        st.markdown("---")
        
        df_prov_si = (
            df_opt_tab2
            .groupby("provinsi")["actual_tonase_in"]
            .sum()
            .reset_index()
        )
        df_prov_so = (
            df_opt_tab2
            .groupby(["provinsi", "week_start", "kode_gudang"])["total_sellout_gudang"]
            .first()
            .groupby("provinsi")
            .sum()
            .reset_index()
        )
        df_prov_stock = pd.merge(df_prov_si, df_prov_so, on="provinsi", how="left")

        df_prov_stock["coverage_ratio"] = (
            df_prov_stock["actual_tonase_in"]
            / df_prov_stock["total_sellout_gudang"].replace(0, np.nan)
        ).fillna(0)

        fig3 = go.Figure(data=[
            go.Bar(
                name="Volume Masuk (Sell-In)",
                x=df_prov_stock["provinsi"],
                y=df_prov_stock["actual_tonase_in"],
                marker_color="#2c3e50",
            ),
            go.Bar(
                name="Volume Terserap (Sell-Out)",
                x=df_prov_stock["provinsi"],
                y=df_prov_stock["total_sellout_gudang"],
                marker_color="#e67e22",
            ),
        ])
        fig3.update_layout(
            barmode="group",
            title="Sell-In vs Sell-Out Volume per Provinsi",
            hovermode="x unified",
            template="plotly_white",
        )
        st.plotly_chart(fig3, use_container_width=True)

        under_supplied = df_prov_stock[
            df_prov_stock["coverage_ratio"] < COVERAGE_LOWER
        ]["provinsi"].tolist()

        over_stocked = df_prov_stock[
            df_prov_stock["coverage_ratio"] > COVERAGE_UPPER
        ]["provinsi"].tolist()

        if under_supplied:
            st.markdown(
                f'<div class="alert-red">'
                f'<b>⚠️ Defisit Pasokan (SI/SO < {COVERAGE_LOWER}):</b> '
                f'{", ".join(under_supplied)}.<br>'
                f'Pasokan masuk lebih kecil dari penyerapan demand — '
                f'wilayah ini membutuhkan injeksi stok Sell-In tambahan.'
                f'</div>',
                unsafe_allow_html=True,
            )
        if over_stocked:
            st.markdown(
                f'<div class="alert-yellow">'
                f'<b>⚠️ Surplus Pasokan (SI/SO > {COVERAGE_UPPER}):</b> '
                f'{", ".join(over_stocked)}.<br>'
                f'Pasokan masuk melebihi penyerapan demand — '
                f'terdapat akumulasi stok yang perlu direlokasi atau didorong promosinya.'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ─────────────────────────────────────────────────────────────────
        # 📈 AUDIT RATA-RATA TONASE vs REORDER POINT (ROP) PER GUDANG
        # ─────────────────────────────────────────────────────────────────
        st.subheader("Audit Rata-rata Aktual Tonase Masuk vs Reorder Point (ROP)")
        df_rop = (
            df_opt_tab2
            .groupby("kode_gudang")[["actual_tonase_in", "reorder_point_est"]]
            .mean()
            .reset_index()
        )
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=df_rop["kode_gudang"],
            y=df_rop["actual_tonase_in"],
            name="Avg Actual Tonase In",
            marker_color="#34495e",
        ))
        fig4.add_trace(go.Scatter(
            x=df_rop["kode_gudang"],
            y=df_rop["reorder_point_est"],
            name="Reorder Point (ROP)",
            mode="lines+markers",
            line=dict(color="red", width=2),
        ))
        fig4.update_layout(
            title="Audit Rata-rata Aktual Tonase Masuk vs Reorder Point (ROP) per Kode Gudang",
            hovermode="x unified",
            template="plotly_white",
        )
        st.plotly_chart(fig4, use_container_width=True)

        # ─────────────────────────────────────────────────────────────────
        # 🗺️ ANALISIS UTILISASI GUDANG vs SUPLAI AKTUAL
        # ─────────────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("Analisis Utilisasi Gudang vs Suplai Aktual")
        df_util = (
            df_opt_tab2
            .groupby("kode_gudang")
            .agg(
                total_actual_in=("actual_tonase_in", "sum"),
                total_target_ca=("target_tonase_ca", "sum"),
                avg_actual_in=("actual_tonase_in", "mean")
            )
            .reset_index()
        )
        
        # Hitung rasio secara keseluruhan (menghindari division-by-zero mingguan)
        df_util["utilisasi_vs_ca"] = df_util.apply(
            lambda r: r["total_actual_in"] / r["total_target_ca"] if r["total_target_ca"] > 0 else 0.0,
            axis=1
        )
        
        fig_util = px.scatter(
            df_util,
            x="avg_actual_in",
            y="utilisasi_vs_ca",
            text="kode_gudang",
            size="avg_actual_in",
            color="utilisasi_vs_ca",
            color_continuous_scale="RdYlGn_r",
            title="Peta Utilisasi Gudang (Mendeteksi Overcapacity)",
            labels={
                "avg_actual_in": "Rata-rata Tonase Masuk (Suplai)",
                "utilisasi_vs_ca":  "Utilisasi Kapasitas (rasio SI/CA)",
            },
        )
        fig_util.update_traces(textposition="top center")
        fig_util.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="red",
            annotation_text="Batas Overcapacity (utilisasi = 1.0)",
        )
        st.plotly_chart(fig_util, use_container_width=True)

        st.markdown("---")
        st.subheader("Analisis Keseimbangan Distribusi (Coverage Ratio SI/SO)")

        df_cov = df_prov_stock.sort_values(by="coverage_ratio", ascending=True)

        df_cov["status"] = df_cov["coverage_ratio"].apply(
            lambda x: "Defisit Pasokan (Under-supplied)"
            if x < COVERAGE_LOWER
            else ("Surplus Pasokan (Over-stocked)" if x > COVERAGE_UPPER else "Seimbang (Balanced)")
        )

        fig_cov = px.bar(
            df_cov,
            y="provinsi",
            x="coverage_ratio",
            color="status",
            orientation="h",
            title="Coverage Ratio Pasokan (Sell-In / Sell-Out) per Provinsi",
            labels={
                "coverage_ratio": f"Coverage Ratio SI/SO (Ideal = 1.0)",
                "provinsi":       "Provinsi",
                "status":         "Status Pasokan",
            },
            color_discrete_map=COVERAGE_COLOR_MAP,
        )
        fig_cov.add_vline(
            x=1.0, line_dash="dash", line_color="black",
            annotation_text="Ideal = 1.0",
        )
        fig_cov.add_vline(
            x=COVERAGE_LOWER, line_dash="dot", line_color="#e74c3c",
            annotation_text=f"Batas Defisit ({COVERAGE_LOWER})",
        )
        fig_cov.add_vline(
            x=COVERAGE_UPPER, line_dash="dot", line_color="#3498db",
            annotation_text=f"Batas Surplus ({COVERAGE_UPPER})",
        )
        st.plotly_chart(fig_cov, use_container_width=True)

        st.info(
            f"💡 **Insight Strategis:** Coverage Ratio = Sell-In ÷ Sell-Out (SI/SO) "
            f"mengukur keseimbangan antara pasokan masuk dan penyerapan demand di setiap provinsi.  \n"
            f"- **Rasio < {COVERAGE_LOWER}** *(Defisit)*: pasokan kurang dari permintaan — injeksi stok diprioritaskan.  \n"
            f"- **Rasio > {COVERAGE_UPPER}** *(Surplus)*: akumulasi stok — lakukan relokasi ke provinsi defisit atau dorong promosi.  \n"
            f"- **Rasio {COVERAGE_LOWER}–{COVERAGE_UPPER}** *(Seimbang)*: kondisi distribusi ideal."
        )

        # ── Download ───────────────────────────────────────────────────────
        csv_rop = df_rop.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Unduh Data ROP Gudang (CSV)",
            data=csv_rop,
            file_name="rop_gudang.csv",
            mime="text/csv",
        )

    else:
        st.warning("Tidak ada data stok untuk Material Code yang dipilih.")
