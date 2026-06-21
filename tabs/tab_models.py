import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def render_tab_models(df_rev_filtered, df_opt_filtered, rev_model, stock_model, rev_enc, stock_enc):
    st.header("Sistem Peramalan & Prediksi (Machine Learning)")
    st.markdown("Mensimulasikan hasil dari Model XGBoost / LightGBM yang telah di-training. Alat ini mengambil kondisi logistik pada baris terakhir dari data filter Anda dan memprediksi ekspektasinya.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔮 Simulasi Revenue")
        if not df_rev_filtered.empty:
            # Ambil satu baris acak atau pertama sebagai sampel fitur
            selected_dist = st.selectbox("Pilih Distributor", df_rev_filtered['soldto'].unique())
            sample_data = df_rev_filtered[df_rev_filtered['soldto'] == selected_dist].iloc[-1:]
            
            features = getattr(rev_model, 'feature_name_', getattr(rev_model, 'feature_names_in_', None))
            if features is not None:
                X = sample_data.reindex(columns=features, fill_value=0).copy()
                try:
                    for col, encoder in rev_enc.items():
                        if col in X.columns:
                            known_classes = list(encoder.classes_)
                            X[col] = X[col].apply(lambda x: x if x in known_classes else known_classes[0])
                            X[col] = encoder.transform(X[col])
                            
                    prediction = rev_model.predict(X)[0]
                    aktual = sample_data['target_revenue'].values[0]
                    delta = prediction - aktual
                    delta_pct = (delta / aktual) * 100 if aktual != 0 else 0
                    
                    st.metric("Prediksi Target Revenue", f"Rp {prediction:,.0f}", f"{delta_pct:+.2f}% vs Baseline")
                    st.caption(f"Aktual Target Revenue (Baseline): **Rp {aktual:,.0f}**")
                    
                    # Tambahan Best Practice: Feature Importance (Driver Analisis)
                    importances = getattr(rev_model, 'feature_importances_', None)
                    if importances is not None:
                        df_imp = pd.DataFrame({'Fitur': features, 'Kepentingan': importances}).sort_values(by='Kepentingan', ascending=False).head(5)
                        fig_imp = px.bar(df_imp, x='Kepentingan', y='Fitur', orientation='h', title="Top 5 Driver (Fitur) Pendorong Prediksi", template="plotly_white", color_discrete_sequence=['#3498db'])
                        fig_imp.update_layout(yaxis={'categoryorder':'total ascending'}, height=300)
                        st.plotly_chart(fig_imp, use_container_width=True)
                        st.info("💡 **Insight:** Faktor-faktor di atas adalah yang paling berkontribusi terhadap hasil prediksi Revenue.")

                except Exception as e:
                    st.error(f"Error prediksi revenue: {e}")
            else:
                st.warning("Model revenue tidak memiliki metadata fitur.")
        else:
            st.warning("Data revenue kosong.")
            
    with col2:
        st.subheader("🚚 Simulasi Kebutuhan Stok")
        if not df_opt_filtered.empty:
            selected_wh = st.selectbox("Pilih Gudang", df_opt_filtered['kode_gudang'].unique())
            sample_data = df_opt_filtered[df_opt_filtered['kode_gudang'] == selected_wh].iloc[-1:]
            
            features = getattr(stock_model, 'feature_name_', getattr(stock_model, 'feature_names_in_', None))
            if features is not None:
                X = sample_data.reindex(columns=features, fill_value=0).copy()
                try:
                    for col, encoder in stock_enc.items():
                        if col in X.columns:
                            known_classes = list(encoder.classes_)
                            X[col] = X[col].apply(lambda x: x if x in known_classes else known_classes[0])
                            X[col] = encoder.transform(X[col])
                            
                    prediction = stock_model.predict(X)[0]
                    aktual = sample_data['actual_tonase_in'].values[0]
                    delta = prediction - aktual
                    delta_pct = (delta / aktual) * 100 if aktual != 0 else 0
                    
                    st.metric("Prediksi Kebutuhan Suplai (Tonase In)", f"{prediction:,.2f} TON", f"{delta_pct:+.2f}% vs Baseline")
                    st.caption(f"Aktual Tonase In (Baseline): **{aktual:,.2f} TON**")
                    
                    # Tambahan Best Practice: Feature Importance (Driver Analisis)
                    importances = getattr(stock_model, 'feature_importances_', None)
                    if importances is not None:
                        df_imp = pd.DataFrame({'Fitur': features, 'Kepentingan': importances}).sort_values(by='Kepentingan', ascending=False).head(5)
                        fig_imp = px.bar(df_imp, x='Kepentingan', y='Fitur', orientation='h', title="Top 5 Driver Kebutuhan Stok", template="plotly_white", color_discrete_sequence=['#e67e22'])
                        fig_imp.update_layout(yaxis={'categoryorder':'total ascending'}, height=300)
                        st.plotly_chart(fig_imp, use_container_width=True)
                        st.info("💡 **Insight:** Fitur di atas mendominasi pola pergerakan pasokan stok di gudang ini.")
                        
                except Exception as e:
                    st.error(f"Error prediksi stok: {e}")
            else:
                st.warning("Model stok tidak memiliki metadata fitur.")
        else:
            st.warning("Data stok kosong.")
