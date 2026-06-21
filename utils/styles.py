import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            height: 100%;
            min-height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-title {
            font-size: 14px;
            color: #7f8c8d;
        }
        .alert-red {
            background-color: #ffcccc;
            padding: 10px;
            border-radius: 5px;
            color: #cc0000;
            margin-top: 10px;
        }
        .alert-yellow {
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            color: #856404;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
