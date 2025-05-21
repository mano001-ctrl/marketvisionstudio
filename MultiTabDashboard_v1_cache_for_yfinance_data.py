# --- Import libraries ---
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import scipy.optimize as sco

sns.set_theme(style="whitegrid")

# --- Caching Yahoo Finance functions ---
@st.cache_data(ttl=3600)
def load_prices(tickers, start, end):
    return yf.download(tickers, start=start, end=end, progress=False)["Close"]

@st.cache_data(ttl=3600)
def load_roe(ticker_list):
    roe_ratios = {}
    for ticker in ticker_list:
        try:
            info = yf.Ticker(ticker).info
            roe_ratios[ticker] = info.get('returnOnEquity', None)
        except Exception:
            roe_ratios[ticker] = None
    return roe_ratios

# --- Tabs ---
tab = st.selectbox(
    "Select Dashboard Section",
    ["Portfolio Dashboard", "Rolling Returns Heatmap", "Return on Equity Heatmap", "Strategy Development"]
)

# --- Sidebar (dynamic) ---
if tab == "Portfolio Dashboard":
    st.sidebar.header("Settings: Portfolio Dashboard")
    selected_stocks = st.sidebar.multiselect(
        "Select one or more stocks:",
        ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'UNH'],
        default=['AAPL', 'MSFT'],
        key="portfolio_stocks"
    )
    start_date = st.sidebar.date_input("Start date", pd.to_datetime("2022-01-01"), key="portfolio_start")
    end_date = st.sidebar.date_input("End date", pd.to_datetime("today"), key="portfolio_end")

elif tab == "Rolling Returns Heatmap":
    st.sidebar.header("Settings: Rolling Returns Heatmap")
    rolling_ticker = st.sidebar.text_input("Ticker for rolling heatmap", value="SPY", key="heatmap_ticker")
    rolling_start_date = st.sidebar.date_input("Start date", pd.to_datetime("today") - pd.Timedelta(days=30), key="heatmap_start")
    rolling_end_date = st.sidebar.date_input("End date", pd.to_datetime("today"), key="heatmap_end")

    st.sidebar.header("Settings: Sector/Commodity/Currency Heatmap")
    sector_start = st.sidebar.date_input("Start date for sector heatmap", pd.to_datetime("today") - pd.Timedelta(days=60), key="sector_start")
    sector_end = st.sidebar.date_input("End date for sector heatmap", pd.to_datetime("today"), key="sector_end")

elif tab == "Return on Equity Heatmap":
    st.sidebar.header("No settings required for ROE Heatmap.")

elif tab == "Strategy Development":
    st.sidebar.header("Settings: Strategy Development")
    tsmom_ticker = st.sidebar.text_input("Enter ticker for TSMOM", value="AAPL", key="tsmom_ticker")
    tsmom_lookback = st.sidebar.slider("Lookback Period (days)", 30, 365, 90, key="tsmom_lookback")
    tsmom_start = st.sidebar.date_input("Start date", pd.to_datetime("2022-01-01"), key="tsmom_start")
    tsmom_end = st.sidebar.date_input("End date", pd.to_datetime("today"), key="tsmom_end")

# --- Main Area Content ---
if tab == "Portfolio Dashboard":
    st.header("📊 Simple Portfolio Performance Dashboard")
    if selected_stocks:
        prices = load_prices(selected_stocks, start_date, end_date)
        daily_returns = prices.pct_change().dropna()

        st.subheader("Price Data")
        st.line_chart(prices)

        st.subheader("Daily Returns")
        st.line_chart(daily_returns)

        st.subheader("Data Table")
        st.dataframe(prices)

elif tab == "Rolling Returns Heatmap":
    st.header("📈 Rolling Daily Average Returns Calendar Heatmap")

    data = load_prices(rolling_ticker, rolling_start_date, rolling_end_date)
    daily_returns = data.pct_change().dropna() * 100

    if not daily_returns.empty:
        calendar_data = daily_returns.reset_index()
        calendar_data.columns = ['Date', 'Return']
        calendar_data['Year'] = calendar_data['Date'].dt.year
        calendar_data['Month'] = calendar_data['Date'].dt.month
        calendar_data['Day'] = calendar_data['Date'].dt.day
        calendar_data['Week'] = calendar_data['Date'].dt.isocalendar().week
        calendar_data['Weekday'] = calendar_data['Date'].dt.weekday

        pivot = calendar_data.pivot(index='Week', columns='Weekday', values='Return')
        weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        pivot.columns = weekday_labels[:len(pivot.columns)]

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(pivot, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5, ax=ax)
        plt.title(f"Rolling Daily Average Returns\n({rolling_start_date} to {rolling_end_date})", fontsize=16)
        plt.xlabel("Day of Week")
        plt.ylabel("Week")
        st.pyplot(fig)

        # <<< ADD THE DATA TABLE DISPLAY HERE >>>
        st.subheader("Rolling Returns Data Table")
        st.dataframe(daily_returns)

    st.markdown("---")

    st.header("🌍 Sector, Commodity, and Currency Heatmap")

    sector_instruments = {
        "XLF": "Financials", "XLY": "Consumer Discretionary", "XLV": "Healthcare", "XLI": "Industrials",
        "XLE": "Energy", "XLP": "Consumer Staples", "XLK": "Technology", "XLU": "Utilities",
        "XLB": "Materials", "XLRE": "Real Estate", "GLD": "Gold", "USO": "Crude Oil",
        "UNG": "Natural Gas", "SLV": "Silver", "UUP": "US Dollar", "FXE": "Euro",
        "FXY": "Japanese Yen", "FXB": "British Pound"
    }
    tickers = list(sector_instruments.keys())

    sector_prices = load_prices(tickers, sector_start, sector_end)
    sector_prices = sector_prices.dropna(how='all')
    recent_sector_prices = sector_prices.tail(20)
    sector_returns = recent_sector_prices.pct_change() * 100
    sector_heatmap_data = sector_returns.T
    sector_heatmap_data.index = [sector_instruments[t] for t in sector_heatmap_data.index]

    fig2, ax2 = plt.subplots(figsize=(14, 10))
    sns.heatmap(sector_heatmap_data, annot=True, fmt=".2f", cmap="RdYlGn", center=0, linewidths=0.5, ax=ax2,
                cbar_kws={'label': 'Daily Return (%)'})
    plt.title("Sector, Commodity, and Currency Daily Returns\n(Last 20 Trading Days)", fontsize=16)
    plt.xlabel("Date")
    plt.ylabel("Instrument")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig2)
    st.subheader("Sector, Commodity, and Currency Returns Data Table")
    st.dataframe(sector_returns.T)


elif tab == "Return on Equity Heatmap":
    st.header("📈 Return on Equity (ROE) Heatmap: 30 Largest S&P500 Stocks")

    largest_30 = [
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'TSLA', 'BRK-B',
        'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC',
        'XOM', 'CMCSA', 'ADBE', 'NFLX', 'VZ', 'INTC', 'T', 'KO', 'PFE',
        'MRK', 'CSCO', 'PEP'
    ]

    roe_ratios = load_roe(largest_30)
    chunk_size = 5
    n_rows = len(largest_30) // chunk_size
    roe_matrix = np.full((n_rows, chunk_size), np.nan)
    annot_matrix_roe = np.empty((n_rows, chunk_size), dtype=object)

    for i, ticker in enumerate(largest_30):
        row = i // chunk_size
        col = i % chunk_size
        roe_val = roe_ratios[ticker]
        roe_matrix[row, col] = roe_val if roe_val is not None else np.nan
        annot_matrix_roe[row, col] = f"{ticker}\n{roe_val:.2f}" if roe_val is not None else f"{ticker}\nN/A"

    df_roe = pd.DataFrame(roe_matrix, index=[f"Row {r+1}" for r in range(n_rows)], columns=[f"Col {c+1}" for c in range(chunk_size)])

    min_roe = np.nanmin(roe_matrix)
    max_roe = np.nanmax(roe_matrix)
    mean_roe = np.nanmean(roe_matrix)

    fig_roe, ax_roe = plt.subplots(figsize=(10, 6))
    sns.heatmap(df_roe, cmap='RdYlGn', annot=annot_matrix_roe, fmt='', linewidths=0.5,
                center=mean_roe, vmin=min_roe, vmax=max_roe, cbar_kws={'label': 'Return on Equity'}, ax=ax_roe)
    ax_roe.set_title("Return on Equity for 30 Largest S&P 500 Stocks\n(6 rows × 5 columns)", fontsize=14, pad=12)
    ax_roe.set_xlabel("Column Index", fontsize=12)
    ax_roe.set_ylabel("Row Index", fontsize=12)
    st.pyplot(fig_roe)

    st.markdown("---")

    st.header("🏦 Debt-to-Equity (D/E) Ratio Heatmap: 30 Largest S&P500 Stocks")
    de_ratios = {}
    for ticker in largest_30:
        try:
            info = yf.Ticker(ticker).info
            de_value = info.get('debtToEquity', None)
            if de_value is not None:
                de_value = de_value / 100.0
            de_ratios[ticker] = de_value
        except Exception:
            de_ratios[ticker] = None

    de_matrix = np.full((n_rows, chunk_size), np.nan)
    annot_matrix_de = np.empty((n_rows, chunk_size), dtype=object)

    for i, ticker in enumerate(largest_30):
        row = i // chunk_size
        col = i % chunk_size
        de_val = de_ratios[ticker]
        de_matrix[row, col] = de_val if de_val is not None else np.nan
        annot_matrix_de[row, col] = f"{ticker}\n{de_val:.2f}" if de_val is not None else f"{ticker}\nN/A"

    df_de = pd.DataFrame(de_matrix, index=[f"Row {r+1}" for r in range(n_rows)], columns=[f"Col {c+1}" for c in range(chunk_size)])

    min_de = np.nanmin(de_matrix)
    max_de = np.nanmax(de_matrix)
    mean_de = np.nanmean(de_matrix)

    fig_de, ax_de = plt.subplots(figsize=(10, 6))
    sns.heatmap(df_de, cmap='RdYlGn_r', annot=annot_matrix_de, fmt='', linewidths=0.5,
                center=mean_de, vmin=min_de, vmax=max_de, cbar_kws={'label': 'Debt-to-Equity Ratio (Decimal)'}, ax=ax_de)
    ax_de.set_title("Debt-to-Equity Ratios (Decimal) for 30 Largest S&P 500 Stocks\n(6 rows × 5 columns)", fontsize=14, pad=12)
    ax_de.set_xlabel("Column Index", fontsize=12)
    ax_de.set_ylabel("Row Index", fontsize=12)
    st.pyplot(fig_de)

# --- Tab 4: Strategy Development ---

elif tab == "Strategy Development":
    st.header("🚀 Strategy Development")

    # --- Main Area Inputs ---
    st.subheader("Time Series Momentum Strategy")

    tsmom_ticker = tsmom_ticker
    lookback_days = tsmom_lookback
    start_tsmom_date = tsmom_start
    end_tsmom_date = tsmom_end

    ts_data = yf.download(tsmom_ticker, start=start_tsmom_date, end=end_tsmom_date)["Close"]

    if ts_data.empty:
        st.error("No data found for the selected ticker.")
    else:
        returns = ts_data.pct_change().dropna()
        lookback_returns = ts_data.pct_change(periods=lookback_days).shift(1)
        signal = (lookback_returns > 0).astype(int)
        strategy_returns = signal * returns
        cumulative_strategy = (1 + strategy_returns).cumprod()
        cumulative_buy_hold = (1 + returns).cumprod()

        fig3, ax3 = plt.subplots(figsize=(10, 6))
        ax3.plot(cumulative_buy_hold, label="Buy & Hold", linestyle="--")
        ax3.plot(cumulative_strategy, label="TS Momentum Strategy", linewidth=2)
        ax3.set_title(f"TSMOM vs Buy & Hold ({tsmom_ticker})", fontsize=16)
        ax3.set_xlabel("Date")
        ax3.set_ylabel("Growth of $1 Investment")
        ax3.legend()
        st.pyplot(fig3)

    # --- Divider ---
    st.markdown("---")

    # --- Buy and Hold 10-Stock Portfolio ---
    st.subheader("📈 Buy & Hold 10-Stock Portfolio")

    portfolio_tickers = st.multiselect(
        "Select 10 stocks for portfolio:",
        [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'UNH',
            'V', 'PG', 'XOM', 'BAC', 'WMT'
        ],
        default=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
        key="buyhold_portfolio"
    )

    if len(portfolio_tickers) < 2:
        st.warning("Please select at least 2 stocks.")
    else:
        port_prices = yf.download(portfolio_tickers, start=start_tsmom_date, end=end_tsmom_date)["Close"]
        port_returns = port_prices.pct_change().dropna()
        equal_weight_returns = port_returns.mean(axis=1)

        spy_prices = yf.download("SPY", start=start_tsmom_date, end=end_tsmom_date)["Close"]
        spy_returns = spy_prices.pct_change().dropna()

        spy_returns = spy_returns.reindex(equal_weight_returns.index).dropna()
        cumulative_portfolio = (1 + equal_weight_returns).cumprod()
        cumulative_spy = (1 + spy_returns).cumprod()

        fig4, ax4 = plt.subplots(figsize=(10, 6))
        ax4.plot(cumulative_portfolio, label="10-Stock Portfolio", linewidth=2)
        ax4.plot(cumulative_spy, label="SPY Benchmark", linestyle="--")
        ax4.set_title("Buy & Hold Portfolio vs SPY", fontsize=16)
        ax4.set_xlabel("Date")
        ax4.set_ylabel("Growth of $1 Investment")
        ax4.legend()
        st.pyplot(fig4)

    # --- Divider ---
    st.markdown("---")
       # --- Tab: Strategy Development ---
    st.header("🎯 Strategy Development (Clean Efficient Frontier)")

# Define 50 largest S&P 500 stocks
    top_50_stocks = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'TSLA', 'BRK-B', 'NVDA', 'JPM',
    'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC', 'XOM', 'CMCSA', 'ADBE', 'NFLX',
    'VZ', 'INTC', 'T', 'KO', 'PFE', 'MRK', 'CSCO', 'PEP', 'WMT', 'CVX', 'ABBV', 'AVGO',
    'COST', 'MCD', 'ACN', 'DHR', 'AMD', 'QCOM', 'TXN', 'LLY', 'LIN', 'NEE', 'PM', 'AMGN',
    'LOW', 'HON', 'UNP'
]

# --- User Input ---
    user_selected_stocks = st.multiselect(
    "Select up to 30 stocks for your strategy:",
    top_50_stocks,
    default=top_50_stocks[:30],
    max_selections=30,
    key="user_stock_selection_clean"
)

    if len(user_selected_stocks) < 2:
        st.warning("Please select at least 2 stocks to continue.")
    else:
        # --- Data Fetching ---
        @st.cache_data
        def load_prices(tickers, start_date, end_date):
            data = yf.download(tickers, start=start_date, end=end_date, progress=False)["Close"]
            return data.dropna(axis=1)

    start_date = "2018-01-01"
    end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    prices = load_prices(user_selected_stocks, start_date, end_date)

    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    num_assets = len(mean_returns)
    rf_rate = 0.02  # Risk-free rate

    # --- Optimization functions ---
    def portfolio_performance(weights, mean_returns, cov_matrix):
        ret = np.sum(mean_returns * weights)
        vol = np.sqrt(weights.T @ cov_matrix @ weights)
        return ret, vol

    def min_variance(mean_returns, cov_matrix, target_return):
        num_assets = len(mean_returns)
        args = (cov_matrix, )

        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: portfolio_performance(x, mean_returns, cov_matrix)[0] - target_return}
        ]
        bounds = tuple((0, 1) for _ in range(num_assets))

        result = sco.minimize(lambda x: portfolio_performance(x, mean_returns, cov_matrix)[1],
                              num_assets*[1./num_assets,], method='SLSQP',
                              bounds=bounds, constraints=constraints)
        return result

    # --- Calculate Efficient Frontier ---
    target_returns = np.linspace(mean_returns.min(), mean_returns.max(), 100)
    frontier_volatility = []

    for ret in target_returns:
        res = min_variance(mean_returns, cov_matrix, ret)
        if res.success:
            frontier_volatility.append(res.fun)
        else:
            frontier_volatility.append(np.nan)

    # --- Find max Sharpe portfolio ---
    def neg_sharpe(weights, mean_returns, cov_matrix, rf_rate):
        ret, vol = portfolio_performance(weights, mean_returns, cov_matrix)
        return -(ret - rf_rate) / vol

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))

    max_sharpe_result = sco.minimize(neg_sharpe, num_assets*[1./num_assets,],
                                     args=(mean_returns, cov_matrix, rf_rate),
                                     method='SLSQP', bounds=bounds, constraints=constraints)

    max_sharpe_ret, max_sharpe_vol = portfolio_performance(max_sharpe_result.x, mean_returns, cov_matrix)

    # --- Find min variance portfolio ---
    min_vol_result = sco.minimize(lambda x: portfolio_performance(x, mean_returns, cov_matrix)[1],
                                  num_assets*[1./num_assets,],
                                  method='SLSQP', bounds=bounds, constraints=constraints)

    min_vol_ret, min_vol_vol = portfolio_performance(min_vol_result.x, mean_returns, cov_matrix)

    # --- Plot ---
    fig = go.Figure()

    # Plot the efficient frontier
    fig.add_trace(go.Scatter(
        x=frontier_volatility,
        y=target_returns,
        mode='lines',
        line=dict(color='white', width=2),
        name='Efficient Frontier'
    ))

    # Plot the Capital Market Line
    cml_x = np.linspace(0, max(frontier_volatility), 100)
    cml_y = rf_rate + ((max_sharpe_ret - rf_rate) / max_sharpe_vol) * cml_x
    fig.add_trace(go.Scatter(
        x=cml_x,
        y=cml_y,
        mode='lines',
        line=dict(color='red', dash='dot'),
        name='Capital Market Line'
    ))

    # Plot Max Sharpe Portfolio
    fig.add_trace(go.Scatter(
        x=[max_sharpe_vol],
        y=[max_sharpe_ret],
        mode='markers+text',
        marker=dict(color='blue', size=12, symbol='star'),
        text=["Max Sharpe"],
        textposition='top center',
        name='Max Sharpe'
    ))

    # Plot Min Variance Portfolio
    fig.add_trace(go.Scatter(
        x=[min_vol_vol],
        y=[min_vol_ret],
        mode='markers+text',
        marker=dict(color='green', size=12, symbol='star'),
        text=["Min Volatility"],
        textposition='bottom center',
        name='Min Volatility'
    ))
    # Plot individual stocks
    # Plot individual stocks with hover labels only (cleaner)
    individual_vols = returns.std() * np.sqrt(252)  # Annualized volatility
    individual_returns = mean_returns  # Already annualized

    fig.add_trace(go.Scatter(
    x=individual_vols,
    y=individual_returns,
    mode='markers',
    marker=dict(
        color='lime',
        size=8,
        symbol='circle'
    ),
    text=individual_vols.index,  # Stock tickers
    hovertemplate='<b>%{text}</b><br>Volatility: %{x:.2%}<br>Return: %{y:.2%}',
    name='Individual Stocks'
))


    
    go.Figure().update_layout(
    title=dict(
        text="12-Months Period Efficient Frontier (User Selected Stocks)",
        font=dict(color="black", size=20)  # <<< Set title text color to black + optional size increase
    ),
    xaxis_title="Risk (Volatility)",
    yaxis_title="Return",
    xaxis_tickformat=".0%",
    yaxis_tickformat=".0%",
    template="plotly_white",
    width=950,
    height=600,
    showlegend=True,
    hovermode="closest",
    paper_bgcolor="white",
    legend=dict(
        font=dict(
            color="black",
            size=14  # (optional) make the legend text a little larger too
        )
    )
)

    st.plotly_chart(fig, use_container_width=True)
