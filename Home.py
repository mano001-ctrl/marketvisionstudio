import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Title
st.title("Simple Portfolio Performance Dashboard")

# Sidebar inputs
st.sidebar.header("User Input Features")
tickers = st.sidebar.multiselect(
    "Select one or more stocks:",
    ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META'],
    ['AAPL', 'MSFT']  # default selection
)

start_date = st.sidebar.date_input("Start date", pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End date", pd.to_datetime("today"))

# Download price datas
if tickers:
    data = yf.download(tickers, start=start_date, end=end_date)["Close"]

    st.subheader("Price Data")
    st.line_chart(data)

    # Calculate daily returns
    returns = data.pct_change().dropna()

    st.subheader("Daily Returns")
    st.line_chart(returns)

    # Show table
    st.subheader("Data Table")
    st.dataframe(data)
else:
    st.warning("Please select at least one stock.")

