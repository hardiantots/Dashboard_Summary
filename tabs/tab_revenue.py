import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.llm_engine import generate_executive_briefing

def render_tab_revenue(df_rev_filtered, df_surv_filtered, api_key):
    st.header("Analisis Komersial & Revenue")
    
    # ---------------------------------------------------------
    # Injeksi OpenRouter LLM Reasoning Engine (Executive Briefing)
    # ---------------------------------------------------------
    st.markdown("### 🤖 AI Executive Briefing (OpenRouter + Nemotron)")
    if st.button("Generate Wawasan Eksekutif (AI)", type="primary"):
        with st.spinner("Menyintesis wawasan deterministik dari data terfilter..."):
            briefing = generate_executive_briefing(df_rev_filtered, df_surv_filtered, api_key)
            st.info(briefing)
    st.markdown("---")
    
    # Visualisasi 1: Tren Pendapatan Sell-In Bulanan
    df_rev_trend = df_rev_filtered.groupby(pd.Grouper(key='periode', freq='ME'))['target_revenue'].sum().reset_index()
    if not df_rev_trend.empty:
        fig1 = px.line(df_rev_trend, x='periode', y='target_revenue', markers=True, 
                       title="Tren Pendapatan Sell-In Bulanan 2026",
                       labels={"periode": "Periode", "target_revenue": "Total Pendapatan (Rp)"},
                       template="plotly_white")
        fig1.update_traces(line_color="#2ecc71", line_width=3)
        fig1.update_layout(hovermode="x unified")
        
        max_idx = df_rev_trend['target_revenue'].idxmax()
        max_row = df_rev_trend.loc[max_idx]
        max_val_miliar = max_row['target_revenue'] / 1e9
        fig1.add_annotation(
            x=max_row['periode'],
            y=max_row['target_revenue'],
            text=f"Puncak: Rp {max_val_miliar:.1f} Miliar",
            showarrow=True,
            arrowhead=1,
            yshift=10
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Visualisasi 2: Analisis Pareto Kontribusi Distributor
    df_pareto = df_rev_filtered.groupby('soldto')['target_revenue'].sum().sort_values(ascending=False).reset_index()
    df_pareto['cumulative_perc'] = df_pareto['target_revenue'].cumsum() / df_pareto['target_revenue'].sum() * 100
    
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Bar(x=df_pareto['soldto'], y=df_pareto['target_revenue'], name="Revenue", marker_color='#3498db'), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df_pareto['soldto'], y=df_pareto['cumulative_perc'], name="Cumulative %", mode='lines+markers', line=dict(color='#e74c3c')), secondary_y=True)
    
    fig2.update_layout(title_text="Analisis Pareto Kontribusi Distributor", hovermode="x unified", template="plotly_white")
    fig2.update_xaxes(title_text="Distributor (Sold-To)")
    fig2.update_yaxes(title_text="Total Revenue (Rp)", secondary_y=False)
    fig2.update_yaxes(title_text="Cumulative %", range=[0, 105], secondary_y=True)
    fig2.add_hline(y=80, line_dash="dash", line_color="black", secondary_y=True, annotation_text="Batas 80%")
    st.plotly_chart(fig2, use_container_width=True)
    
    st.info('💡 **Temuan ExDA**: Top 78 dari 102 distributor aktif menyumbang 80% total revenue. Distribusi tergolong sehat dan proporsional (tidak terlalu skewed ke segmen segelintir distributor).')
    
    st.markdown("---")
    
    # Visualisasi 3: Revenue Berdasarkan Provinsi (Tambahan dari EDA Notebook)
    df_prov_rev = df_rev_filtered.groupby('province_desc')['target_revenue'].sum().reset_index().sort_values(by='target_revenue', ascending=True)
    fig3 = px.bar(df_prov_rev, x='target_revenue', y='province_desc', orientation='h',
                  title="Kontribusi Revenue Berdasarkan Provinsi",
                  labels={"target_revenue": "Total Revenue (Rp)", "province_desc": "Provinsi"},
                  template="plotly_white", color='target_revenue', color_continuous_scale="Viridis")
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("### Top 10 Distributor Berdasarkan Revenue")
    df_top10 = df_pareto.head(10).copy()
    
    # Menambahkan nama distributor dari data survey jika tersedia
    if not df_surv_filtered.empty and 'distributor_code' in df_surv_filtered.columns:
        mapping_dist = df_surv_filtered[['distributor_code', 'distributor_name']].dropna().drop_duplicates()
        df_top10 = df_top10.merge(mapping_dist, left_on='soldto', right_on='distributor_code', how='left')
        if 'distributor_name' in df_top10.columns:
            df_top10['distributor_name'] = df_top10['distributor_name'].fillna('Tidak Diketahui')
            # Pindahkan kolom ke posisi kedua
            cols = list(df_top10.columns)
            cols.insert(1, cols.pop(cols.index('distributor_name')))
            df_top10 = df_top10[cols]
    
    # Ubah format nominal agar memiliki pemisah ribuan (koma/titik)
    df_top10['target_revenue_fmt'] = df_top10['target_revenue'].apply(lambda x: f"Rp {x:,.0f}")
    
    st.dataframe(
        df_top10, 
        use_container_width=True,
        column_config={
            "soldto": st.column_config.TextColumn("Kode Distributor"),
            "distributor_name": st.column_config.TextColumn("Nama Distributor"),
            "target_revenue_fmt": st.column_config.TextColumn("Total Revenue"),
            "target_revenue": None, # Sembunyikan kolom asli
            "cumulative_perc": st.column_config.NumberColumn(
                "Persentase Kumulatif",
                format="%.2f %%"
            ),
            "distributor_code": None  # Sembunyikan kolom duplikat
        },
        hide_index=True
    )
    
    csv_pareto = df_pareto.to_csv(index=False).encode('utf-8')
    st.download_button("Unduh Data Pareto (CSV)", data=csv_pareto, file_name="pareto_distributor.csv", mime="text/csv")

