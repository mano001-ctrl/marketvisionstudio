import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import datetime

# --- Streamlit Page Config ---
st.title("Rolling Daily Average Returns Calendar Heatmap")

# Sidebar for inputs
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Enter ticker symbol:", value="SPY")

# Dates
today = datetime.date.today()
start_date = today - datetime.timedelta(days=30)

# Download data
data = yf.download(ticker, start=start_date, end=today, interval="1d")['Close']

if data.empty:
    st.error("No data found. Please check the ticker symbol.")
else:
    # Calculate daily returns
    daily_returns = data.pct_change().dropna() * 100
    daily_avg_return = daily_returns  # Only one ticker

    # Prepare for calendar plotting
    calendar_data = daily_avg_return.reset_index()
    calendar_data.columns = ['Date', 'Return']
    calendar_data['Year'] = calendar_data['Date'].dt.year
    calendar_data['Month'] = calendar_data['Date'].dt.month
    calendar_data['Day'] = calendar_data['Date'].dt.day
    calendar_data['Weekday'] = calendar_data['Date'].dt.weekday
    calendar_data['Week'] = calendar_data['Date'].dt.isocalendar().week

    # Pivot to calendar format
    calendar_pivot = calendar_data.pivot(index='Week', columns='Weekday', values='Return')

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    calendar_pivot.columns = weekday_labels[:len(calendar_pivot.columns)]

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(calendar_pivot, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, linewidths=0.5, ax=ax)
    ax.set_title(f"Rolling Daily Average Returns\n({start_date} to {today})", fontsize=16)
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Week")

    st.pyplot(fig)

    # Show raw data
    with st.expander("Show raw return data"):
        st.dataframe(calendar_data)
