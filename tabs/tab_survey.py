import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def render_tab_survey(df_surv_filtered):
    st.header("Intelijen Operasional Lapangan")
    
    if not df_surv_filtered.empty:
        df_brand = df_surv_filtered.groupby('brand')['total_volume_sales'].sum().reset_index().sort_values(by='total_volume_sales', ascending=False)
        top5_brands = df_brand.head(5)
        
        colors = ['#f39c12' if b == 'TerraBlock' else '#bdc3c7' for b in top5_brands['brand']]
        
        fig5 = px.pie(top5_brands, values='total_volume_sales', names='brand', hole=0.5, 
                      title="Kontribusi Penjualan 5 Produk Teratas",
                      color_discrete_sequence=colors)
        fig5.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig5, use_container_width=True)
        
        st.markdown('**Sorotan Produk**: <span style="color:#f39c12; font-weight:bold;">TerraBlock Semen Portland Komposit</span> mencatatkan performa "High Growth" (+8.5% MoM) di tingkat ritel.', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("Analisis Kesehatan Jaringan: Fill Rate & Stockout Rate")
        df_health = df_surv_filtered.groupby('provinsi')[['avg_fill_rate', 'stockout_rate']].mean().reset_index().sort_values(by='avg_fill_rate', ascending=True)
        
        fig_health = go.Figure()
        fig_health.add_trace(go.Bar(y=df_health['provinsi'], x=df_health['avg_fill_rate'], name='Fill Rate (%)', orientation='h', marker_color='#2ecc71'))
        fig_health.add_trace(go.Bar(y=df_health['provinsi'], x=df_health['stockout_rate'], name='Stockout Rate (%)', orientation='h', marker_color='#e74c3c'))
        fig_health.update_layout(barmode='group', title="Perbandingan Fill Rate vs Stockout Rate Toko per Provinsi",
                                 xaxis_title="Persentase (%)", yaxis_title="Provinsi", template="plotly_white", hovermode="y unified")
        st.plotly_chart(fig_health, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Efektivitas Kunjungan Salesman (Visit vs Sales)")
        df_eff = df_surv_filtered.groupby('salesman')[['n_visits', 'total_volume_sales', 'avg_fill_rate']].mean().reset_index()
        fig_eff = px.scatter(df_eff, x='n_visits', y='total_volume_sales', color='avg_fill_rate', size='total_volume_sales',
                             hover_name='salesman', title="Salesman Visit Effectiveness",
                             labels={'n_visits': 'Rata-rata Kunjungan', 'total_volume_sales': 'Rata-rata Volume Penjualan', 'avg_fill_rate': 'Fill Rate (%)'},
                             color_continuous_scale='Viridis')
        st.plotly_chart(fig_eff, use_container_width=True)
        st.info("💡 **Insight ExDA:** Scatter plot ini mendeteksi apakah frekuensi kunjungan berbanding lurus dengan peningkatan volume sales dan kepuasan pemenuhan pesanan (Fill Rate).")
        
        st.markdown("---")
        st.markdown("### Tabel Interaktif Survei Lapangan")
        df_surv_table = df_surv_filtered.groupby(['salesman', 'provinsi'])[['stockout_rate', 'avg_fill_rate', 'avg_stock_utilization']].mean().reset_index()
        df_surv_table['stockout_rate'] = df_surv_table['stockout_rate'].apply(lambda x: f"{x:.1f}%")
        df_surv_table['avg_fill_rate'] = df_surv_table['avg_fill_rate'].apply(lambda x: f"{x:.1f}%")
        df_surv_table['avg_stock_utilization'] = df_surv_table['avg_stock_utilization'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(
            df_surv_table, 
            use_container_width=True,
            column_config={
                "salesman": st.column_config.TextColumn("Nama Salesman"),
                "provinsi": st.column_config.TextColumn("Provinsi"),
                "stockout_rate": st.column_config.TextColumn("Tingkat Kekosongan (Stockout)"),
                "avg_fill_rate": st.column_config.TextColumn("Rata-rata Fill Rate"),
                "avg_stock_utilization": st.column_config.TextColumn("Utilisasi Stok")
            },
            hide_index=True
        )
        
        csv_surv = df_surv_table.to_csv(index=False).encode('utf-8')
        st.download_button("Unduh Data Survei Lapangan (CSV)", data=csv_surv, file_name="survey_lapangan.csv", mime="text/csv")
    else:
        st.warning("Data survei lapangan tidak tersedia untuk rentang filter saat ini.")
