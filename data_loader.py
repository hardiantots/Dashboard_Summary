import streamlit as st
import pandas as pd
import os
import joblib


@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")

    path_revenue = os.path.join(dataset_dir, "data_for_forecast_revenue.csv")
    path_optim = os.path.join(dataset_dir, "data_for_optimizing.csv")
    path_survey = os.path.join(dataset_dir, "dim_survey.csv")

    # Load Forecast Revenue
    df_revenue = pd.read_csv(path_revenue)
    df_revenue["periode"] = pd.to_datetime(df_revenue["periode"])

    # Load Optimization
    df_optim = pd.read_csv(path_optim)
    df_optim["week_start"] = pd.to_datetime(df_optim["week_start"])

    # Load Survey
    df_survey = pd.read_csv(path_survey)
    df_survey["year_month"] = pd.to_datetime(df_survey["year_month"] + "-01")

    return df_revenue, df_optim, df_survey


@st.cache_resource
def load_models():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")

    rev_model = joblib.load(os.path.join(models_dir, "best_revenue_model.pkl"))
    stock_model = joblib.load(os.path.join(models_dir, "best_stock_model.pkl"))

    rev_enc = joblib.load(os.path.join(models_dir, "encoders_revenue.pkl"))
    stock_enc = joblib.load(os.path.join(models_dir, "encoders_stock.pkl"))

    return rev_model, stock_model, rev_enc, stock_enc
