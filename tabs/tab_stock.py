import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pulp
from utils.llm_engine import generate_dispatch_memo

def render_tab_stock(df_opt_filtered, api_key):
    st.header("Keseimbangan Pasokan & Stok")
    
    # Dictionary Mapping untuk Material Code (Asumsi Bisnis Semen)
    MAT_DICT = {
        "MAT001": "Semen Portland Tipe I",
        "MAT002": "Semen PCC Premium",
        "MAT003": "Semen Tecton Khusus",
        "MAT004": "Semen Portland Komposit",
    }
    
    st.markdown("---")
    st.markdown("### 🎛️ Filter Khusus Modul Stok")
    # Ekstraksi list Material Code unik dengan mapping nama
    list_material_raw = sorted(list(df_opt_filtered['material_code'].dropna().unique()))
    list_material_display = [f"{m} ({MAT_DICT.get(m, 'Produk Umum')})" for m in list_material_raw]
    
    selected_material_display = st.multiselect(
        "Pilih Material Code untuk Analisis Stok di bawah ini:",
        options=list_material_display,
        default=list_material_display
    )
    
    # Kembalikan ke format kode asli untuk filtering
    selected_material = [m.split(" ")[0] for m in selected_material_display]
    
    # Filter dataset khusus untuk tab ini
    df_opt_tab2 = df_opt_filtered.copy()
    if selected_material:
        df_opt_tab2 = df_opt_tab2[df_opt_tab2['material_code'].isin(selected_material)]
        
    if not df_opt_tab2.empty:
        # ---------------------------------------------------------
        # Injeksi Prescriptive Solver (PuLP On-The-Fly)
        # ---------------------------------------------------------
        st.markdown("### ⚡ Prescriptive Solver (PuLP Alokasi Logistik)")
        if st.button("Jalankan Solver Alokasi Logistik (PuLP)", type="primary"):
            with st.spinner("Menjalankan Linear Programming..."):
                try:
                    df_solve = df_opt_tab2.groupby('kode_gudang')[['reorder_point_est', 'target_tonase_ca']].mean().reset_index()
                    # Filter nilai NaN atau 0 agar solver tidak error
                    df_solve = df_solve.dropna()
                    
                    # Asumsi Batas Silo Pabrik Pusat (90% dari total kapasitas gudang jaringan)
                    factory_limit_national = df_solve['target_tonase_ca'].sum() * 0.90
                    
                    # Deklarasi Problem
                    prob = pulp.LpProblem("Logistics_Allocation_Optimization", pulp.LpMaximize)
                    
                    # Decision Variables
                    alloc_vars = pulp.LpVariable.dicts("Alloc", df_solve['kode_gudang'], lowBound=0, cat='Continuous')
                    
                    # Objective: Memaksimalkan total pemenuhan pasokan
                    prob += pulp.lpSum([alloc_vars[i] for i in df_solve['kode_gudang']])
                    
                    # Constraint 1: (Sum X Nasional <= 90% Stok Silo Pabrik Pusat)
                    prob += pulp.lpSum([alloc_vars[i] for i in df_solve['kode_gudang']]) <= factory_limit_national
                    
                    # Constraint 2 & 3: X <= Ramalan ML & X <= Kapasitas Gudang
                    for idx, row in df_solve.iterrows():
                        g_id = row['kode_gudang']
                        prob += alloc_vars[g_id] <= row['reorder_point_est']
                        prob += alloc_vars[g_id] <= row['target_tonase_ca']
                        
                    prob.solve()
                    
                    # Ekstraksi Hasil
                    results = []
                    for idx, row in df_solve.iterrows():
                        g_id = row['kode_gudang']
                        results.append({
                            "Gudang": g_id,
                            "Kapasitas Maks (TON)": row['target_tonase_ca'],
                            "Kebutuhan ML (TON)": row['reorder_point_est'],
                            "Alokasi (TON)": alloc_vars[g_id].varValue
                        })
                    
                    df_pulp = pd.DataFrame(results)
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.success(f"Status Solver: **{pulp.LpStatus[prob.status]}** | Total Alokasi: **{pulp.value(prob.objective):,.0f} TON**")
                        st.dataframe(df_pulp, use_container_width=True, hide_index=True)
                    with col2:
                        st.info(f"Batasan Suplai Silo Pusat (90%): **{factory_limit_national:,.0f} TON**")
                        
                    # ---------------------------------------------------------
                    # Injeksi LLM Reasoning Engine (Dispatch Memo)
                    # ---------------------------------------------------------
                    st.markdown("#### 🤖 AI Dispatch Memo (Surat Instruksi Rebalancing)")
                    with st.spinner("Menyintesis Surat Instruksi Kepala Gudang via OpenRouter..."):
                        memo = generate_dispatch_memo(df_pulp, api_key)
                        st.warning(memo)
                        
                except Exception as e:
                    st.error(f"Gagal menjalankan Solver PuLP: {e}")
        
        st.markdown("---")
        df_prov_stock = df_opt_tab2.groupby('provinsi')[['actual_tonase_in', 'total_sellout_gudang']].sum().reset_index()
        df_prov_stock['coverage_ratio'] = df_prov_stock['actual_tonase_in'] / df_prov_stock['total_sellout_gudang'].replace(0, np.nan)
        
        fig3 = go.Figure(data=[
            go.Bar(name='Volume Masuk (Sell-In)', x=df_prov_stock['provinsi'], y=df_prov_stock['actual_tonase_in'], marker_color='#2c3e50'),
            go.Bar(name='Volume Terserap (Sell-Out)', x=df_prov_stock['provinsi'], y=df_prov_stock['total_sellout_gudang'], marker_color='#e67e22')
        ])
        fig3.update_layout(barmode='group', title="Sell-In vs Sell-Out Volume per Provinsi", hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)
        
        under_supplied = df_prov_stock[df_prov_stock['coverage_ratio'] < 0.90]['provinsi'].tolist()
        over_stocked = df_prov_stock[df_prov_stock['coverage_ratio'] > 1.10]['provinsi'].tolist()
        
        if under_supplied:
            st.markdown(f'<div class="alert-red"><b>⚠️ Under-supplied (Coverage Ratio < 0.90):</b> {", ".join(under_supplied)}.<br>Penyerapan pasar sangat agresif sehingga butuh suntikan stok Sell-In tambahan.</div>', unsafe_allow_html=True)
        if over_stocked:
            st.markdown(f'<div class="alert-yellow"><b>⚠️ Over-stocked (Coverage Ratio > 1.10):</b> {", ".join(over_stocked)}.<br>Terjadi akumulasi barang mati di gudang yang perlu direlokasi atau didorong promosinya.</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("Audit Rata-rata Aktual Tonase Masuk vs Reorder Point (ROP)")
        df_rop = df_opt_tab2.groupby('kode_gudang')[['actual_tonase_in', 'reorder_point_est']].mean().reset_index()
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(x=df_rop['kode_gudang'], y=df_rop['actual_tonase_in'], name='Avg Actual Tonase In', marker_color='#34495e'))
        fig4.add_trace(go.Scatter(x=df_rop['kode_gudang'], y=df_rop['reorder_point_est'], name='Reorder Point (ROP)', mode='lines+markers', line=dict(color='red', width=2)))
        fig4.update_layout(title="Audit Rata-rata Aktual Tonase Masuk vs Reorder Point (ROP) per Kode Gudang", hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Analisis Utilisasi Gudang vs Suplai Aktual")
        df_util = df_opt_tab2.groupby('kode_gudang')[['actual_tonase_in', 'utilisasi_vs_ca']].mean().reset_index()
        fig_util = px.scatter(df_util, x='actual_tonase_in', y='utilisasi_vs_ca', text='kode_gudang', size='actual_tonase_in',
                              color='utilisasi_vs_ca', color_continuous_scale='RdYlGn_r',
                              title="Peta Utilisasi Gudang (Mendeteksi Overcapacity)",
                              labels={'actual_tonase_in': 'Rata-rata Tonase Masuk (Suplai)', 'utilisasi_vs_ca': 'Utilisasi Kapasitas (%)'})
        fig_util.update_traces(textposition='top center')
        fig_util.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Batas Overcapacity (100%)")
        st.plotly_chart(fig_util, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Analisis Keseimbangan Distribusi (Coverage Ratio)")
        df_cov = df_opt_tab2.groupby('provinsi')[['actual_tonase_in', 'total_sellout_gudang']].sum().reset_index()
        df_cov['coverage_ratio'] = df_cov['total_sellout_gudang'] / df_cov['actual_tonase_in']
        df_cov = df_cov.sort_values(by='coverage_ratio', ascending=True)
        
        # Pewarnaan berdasarkan threshold: < 0.9 Under-supplied (Merah), > 1.1 Over-stocked (Biru)
        df_cov['status'] = df_cov['coverage_ratio'].apply(lambda x: 'Under-supplied (Butuh Suplai)' if x < 0.9 else ('Over-stocked (Tahan Suplai)' if x > 1.1 else 'Balanced'))
        color_map = {'Under-supplied (Butuh Suplai)': '#e74c3c', 'Over-stocked (Tahan Suplai)': '#3498db', 'Balanced': '#2ecc71'}
        
        fig_cov = px.bar(df_cov, y='provinsi', x='coverage_ratio', color='status', orientation='h',
                         title="Rasio Penyerapan (Sell-Out / Sell-In) per Provinsi",
                         labels={'coverage_ratio': 'Coverage Ratio (Ideal ~1.0)'}, color_discrete_map=color_map)
        fig_cov.add_vline(x=1.0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_cov, use_container_width=True)
        st.info("💡 **Insight Strategis:** Grafik ini mengidentifikasi wilayah mana yang kelebihan pasokan (Over-stocked) dan kekurangan pasokan (Under-supplied) sehingga perusahaan dapat melakukan *Stock Rebalancing* antar provinsi.")
        

        csv_rop = df_rop.to_csv(index=False).encode('utf-8')
        st.download_button("Unduh Data ROP Gudang (CSV)", data=csv_rop, file_name="rop_gudang.csv", mime="text/csv")
    else:
        st.warning("Tidak ada data stok untuk Material Code yang dipilih.")
