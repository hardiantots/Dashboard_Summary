import streamlit as st

def render_kpi_cards(df_rev_filtered, df_opt_filtered, df_surv_filtered):
    # Perhitungan KPI
    total_revenue = df_rev_filtered['target_revenue'].sum()
    total_sell_in = df_opt_filtered['actual_tonase_in'].sum()
    total_sell_out = df_opt_filtered['total_sellout_gudang'].sum()
    net_stock_delta = total_sell_in - total_sell_out

    avg_fill_rate = df_surv_filtered['avg_fill_rate'].mean() if not df_surv_filtered.empty else 0
    avg_stock_util = df_surv_filtered['avg_stock_utilization'].mean() if not df_surv_filtered.empty else 0

    # Format Values
    if total_revenue >= 1e12:
        rev_str = f"Rp {total_revenue/1e12:.2f} Triliun"
    elif total_revenue >= 1e9:
        rev_str = f"Rp {total_revenue/1e9:.2f} Miliar"
    else:
        rev_str = f"Rp {total_revenue:,.0f}"

    if total_sell_in >= 1e6:
        si_str = f"{total_sell_in/1e6:.2f} Juta TON"
    elif total_sell_in >= 1e3:
        si_str = f"{total_sell_in/1e3:.2f} Ribu TON"
    else:
        si_str = f"{total_sell_in:,.0f} TON"

    if abs(net_stock_delta) >= 1e6:
        delta_str = f"{net_stock_delta/1e6:+.2f} Juta TON"
    elif abs(net_stock_delta) >= 1e3:
        delta_str = f"{net_stock_delta/1e3:+.2f} Ribu TON"
    else:
        delta_str = f"{net_stock_delta:+,.0f} TON"

    delta_color = "🔴" if net_stock_delta > 10000 else ("🟠" if net_stock_delta > 0 else "🟢")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Total Realized Revenue</div><div class="metric-value">{rev_str}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Total Supply Inflow (Sell-In)</div><div class="metric-value">{si_str}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Net Stock Delta (SI - SO)</div><div class="metric-value">{delta_color} {delta_str}</div><div style="font-size:10px; color:gray;">(Penumpukan > 0)</div></div>', unsafe_allow_html=True)
    with col4:
        fr_color = "red" if avg_fill_rate < 80 else "green"
        st.markdown(f'<div class="metric-card"><div class="metric-title">Rata-rata Order Fill Rate</div><div class="metric-value" style="color:{fr_color}">{avg_fill_rate:.1f}%</div><div style="font-size:10px; color:gray;">(< 80% indikasi bottleneck)</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Rata-rata Stock Utilization</div><div class="metric-value">{avg_stock_util:.1f}%</div><div style="font-size:10px; color:gray;">(Gudang hanya terisi ~1/3)</div></div>', unsafe_allow_html=True)
