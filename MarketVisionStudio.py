# --- Import libraries ---
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import scipy.optimize as sco
import plotly.express as px
from plotly.subplots import make_subplots
from fredapi import Fred
import matplotlib.dates as mdates 
from scipy.stats import gaussian_kde




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

@st.cache_data(ttl=3600)
def load_fred_series(codes, start, end):
    fred = Fred(api_key="6dfdc3b09948e0f5a8c23950edce210a")
    df = pd.DataFrame({
        name: fred.get_series(code, start, end)
        for name, code in codes.items()
    })
    df.index = pd.to_datetime(df.index)
    return df.ffill()

# --- Tabs ---
tab = st.selectbox(
    "Select Dashboard Section",
    ["Portfolio Dashboard", "Rolling Returns Heatmap", "Return on Equity Heatmap", "Strategy Development"]
)

# --- Sidebar (dynamic) ---
if tab == "Portfolio Dashboard":
    #st.header("📊 Simple Portfolio Performance Dashboard")

    # --- Sidebar Settings ---
    st.sidebar.header("Settings: Portfolio Dashboard")
    # 1) Stocks
    stock_list = ['AAPL','MSFT','GOOGL','AMZN','TSLA','META','NVDA','JPM','JNJ','V','TQQQ'] 
    selected_stocks = st.sidebar.multiselect(
        "Select Stocks:",
        stock_list,
        default=['AAPL','MSFT'],
        key="portfolio_stocks"
    )
    # 2) Commodities
    comm_list = ["CL=F","SI=F","NG=F"]  # Gold, Crude Oil, Silver, Natural Gas
    selected_comm = st.sidebar.multiselect(
        "Select Commodities:",
        comm_list,
        default=[],
        key="portfolio_comm"
    )
    # 3) Currencies
    fx_list = ["EURUSD=X","JPY=X","GBPUSD=X","AUDUSD=X"] 
    selected_fx = st.sidebar.multiselect(
        "Select FX Rates:",
        fx_list,
        default=[],
        key="portfolio_fx"
    )
    # 4) Crypto
    crypto_list = ["BTC-USD","LTC-USD"] 
    selected_crypto = st.sidebar.multiselect(
        "Select Cryptocurrencies:",
        crypto_list,
        default=["BTC-USD"],
        key="portfolio_crypto"
    )

    # --- Date Range ---
    start_date = st.sidebar.date_input("Start date", pd.to_datetime("2017-01-01"), key="first_portfolio_start")
    end_date   = st.sidebar.date_input("End date",   pd.to_datetime("today"),    key="first_portfolio_end")

    # Combine all instruments
    instruments = selected_stocks + selected_comm + selected_fx + selected_crypto

    if not instruments:
        st.info("Please select at least one instrument to display charts.")
        st.stop()


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


# --- Main Area Content ---
# --- Tab: Portfolio Dashboard ---
# --- Tab: Portfolio Dashboard ---
# --- Main Area Content ---
if tab == "Portfolio Dashboard":
    st.header("📊 Simple Portfolio Performance Dashboard")

    if not selected_stocks:
        st.info("Please select at least one stock to display charts.")
        st.stop()

    # Load price & returns
    prices        = load_prices(instruments, start_date, end_date)
    daily_returns = prices.pct_change().dropna()

    # Chart selector
    chart_choice = st.radio(
        "Select chart to display:",
        ["Price Data", "Interest Rates", "Volatility Indices"],
        horizontal=True,
        key="portfolio_dashboard_chart_choice"
    )

    # ----- PRICE DATA (with Daily Returns underneath) -----
    if chart_choice == "Price Data":
        st.markdown(
        """
        Below is the historical closing price for each of the stocks you selected, plotted over your chosen date range. Use this to see the overall trend, drawdowns, and peaks in the market.
        """
    )
        st.subheader("Price Data")
        #st.line_chart(prices)
        # build your dual‐axis Plotly figure here…
        fig = go.Figure()

    # 1) BTC on the right
        fig.add_trace(go.Scatter(
            x=prices.index,
            y=prices['BTC-USD'],
            name='BTC-USD',
            yaxis='y2',
            line=dict(color='gold')
        ))

        # 2) everything else on the left
        for ticker in [c for c in prices.columns if c != 'BTC-USD']:
            fig.add_trace(go.Scatter(
            x=prices.index,
            y=prices[ticker],
            name=ticker,
            yaxis='y'
        ))

        # 3) Layout tweaks: only BTC axis grid off, legend underneath
        fig.update_layout(
        template='plotly_dark',
        yaxis=dict(
            title='Stock Price',
            showgrid=True
        ),
        yaxis2=dict(
            title='Bitcoin Price',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.25,       # push legend below chart
            yanchor='top'
        ),
        margin=dict(b=140)  # make room under the plot
    )

        st.plotly_chart(fig, use_container_width=True)

        # then your Daily Returns sub‐header, etc…
        st.subheader("Daily Returns")
    

        st.markdown(
    """
    **How to read this chart**  
    - **Multiple tickers:** Each colored line is a different stock; the legend maps color→ticker.  
    - **Trends & extremes:** Look for sustained up- or down-moves, then hover to inspect exact values.  
    - **Interactive zoom:** Click-and-drag on the X-axis to zoom into any period, or use the “🔍” icons.  
    - **Contextual analysis:** Compare drawdowns—where one stock dips while others hold—to spot diversification benefits.
    """
        )
        st.markdown(
            "<span style='color:#FFA500;font-weight:bold;'>🔍 Task:</span> "
            "Scan today’s returns to spot the biggest outlier and investigate its driver.",
            unsafe_allow_html=True,
        )
        st.subheader("Daily Returns")
        st.line_chart(daily_returns)

        # — now display the actual price table —
        st.markdown("---")  # horizontal rule for separation
        st.subheader("Price Data Table")
        st.dataframe(prices)    # shows the closing‐price DataFrame

        st.markdown(
            "> **Tip:** Hover over any bar to see the exact return.  \n"
            "> Use the zoom tool (top-right corner) to isolate a particular period."
        )

        # Monte Carlo simulation only makes sense for one stock at a time
        # Monte Carlo only under its own expander
        st.markdown(
        "<span style='color:#FFA500;font-weight:bold;'>🎲 Monte Carlo Task:</span> "
        "Choose a ticker and tweak the volatility, horizon, and paths to explore a range of possible futures.",
        unsafe_allow_html=True,
)
        with st.sidebar.expander("Monte Carlo Settings", expanded=True):
            # first pick your ticker for the sim
            mc_ticker = st.selectbox(
                    "Ticker for Monte Carlo:",
                    options=['AAPL','MSFT','GOOGL','AMZN','TSLA','META','NVDA','BRK-B','JPM','UNH',
                             "GC=F","CL=F","SI=F","NG=F",
                             "EURUSD=X","JPY=X","GBPUSD=X","AUDUSD=X",
                             "BTC-USD","ETH-USD","LTC-USD"],
                    index=0,
                    key="mc_ticker"
                )
                # fetch its last price
        mc_prices = load_prices([mc_ticker], start_date, end_date)
        if mc_prices.empty:
            st.warning(f"No price data for {mc_ticker}")
        else:
            S0 = mc_prices[mc_ticker].iloc[-1]
            # then the usual parameters
            sigma = st.number_input("Volatility (σ)", min_value=0.0, max_value=1.0,
                                            value=0.21805, step=0.01, key="mc_sigma")
            r     = st.number_input("Risk-free Rate (r)", min_value=0.0, max_value=0.2,
                                            value=0.0495, step=0.001, key="mc_r")
            T     = st.number_input("Horizon (years)", min_value=0.1, max_value=5.0,
                                            value=1.0, step=0.1, key="mc_T")
            N     = st.slider("Time Steps (N)", 50, 500, 180, 10, key="mc_N")
            paths = st.number_input("Number of Paths", 100, 500, 100, 100, key="mc_paths")
            seed  = st.number_input("Random Seed", 0, 9999, 42, 1, key="mc_seed")

            @st.cache_data(ttl=3600)
            def simulate_gbm(S0, sigma, r, T, N, paths, seed):
                np.random.seed(seed)
                dt = T / N
                times = np.linspace(0, T, N+1)
                all_paths = np.zeros((paths, N+1))
                all_paths[:,0] = S0
                for i in range(paths):
                    for t in range(1, N+1):
                        z = np.random.normal()
                        all_paths[i,t] = all_paths[i,t-1] * np.exp(
                                    (r - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*z
                                )
                return times, all_paths

        times, paths_matrix = simulate_gbm(S0, sigma, r, T, N, paths, seed)

        fig_mc = go.Figure()

        # add each simulated path as a semi-transparent line
        for path in paths_matrix:
            fig_mc.add_trace(go.Scatter(
            x=times,
            y=path,
            mode='lines',
            line=dict(color='royalblue', width=1),
            opacity=0.2,
            showlegend=False
        ))

        fig_mc.update_layout(
            #title=f"Monte Carlo Simulation for {mc_ticker}",
            title={
                "text": f"Monte Carlo Simulation for {mc_ticker}",
                "font": {"size": 28}      # ← play with this value
                    },
            xaxis_title="Time (years)",
            yaxis_title="Simulated Stock Price",
            template="plotly_dark",
            hovermode="x unified"
            
            )

        st.plotly_chart(fig_mc, use_container_width=True)
        st.markdown(
        """
        > **🧭 Usage Suggestions:**  
        > - **Increase the Number of Paths** to see a denser “cloud” of outcomes—great for spotting the most probable band.  
        > - **Tweak Volatility (σ)**: What happens if you double it? How does the risk profile change?  
        > - **Extend the Horizon** to 2–5 years to visualize long-term dispersion.  
        > - **Use Different Seeds** to test reproducibility vs. randomness.  
        >  
        > **Explore & Discover:** Adjust parameters in the sidebar and hit “Run” again to uncover hidden risks and opportunities in your chosen ticker’s future.
        """,
        unsafe_allow_html=True,
    )   
        # 1) Compute per‐path statistics
        results = []
        for path in paths_matrix:
            # Compound annual return
            car   = (path[-1] / path[0])**(1 / T) - 1

            # Daily returns & annualized vol
            dr    = np.diff(path) / path[:-1]
            vol   = dr.std() * np.sqrt(252)

            # Sharpe ratio
            sr    = (car - r) / vol if vol > 0 else np.nan

            # — correct drawdown —
            running_max = np.maximum.accumulate(path)
            dd_abs      = (running_max - path) / running_max           # absolute drawdown series
            maxdd       = dd_abs.max()                                 # peak drawdown
            dd95        = np.percentile(dd_abs, 95)                    # 95th pct of absolute drawdowns

            results.append([car, vol, sr, maxdd, dd95])

        df_stats = pd.DataFrame(
            results,
            columns=["CAR","Vol","Sharpe","MaxDD","DD_95"]
        )

        # Convert to percentages
        df_stats[["CAR","Vol","MaxDD","DD_95"]] *= 100

        # 2) Build percentile summary table
        percentiles = [95, 75, 50, 25, 10, 5, 1, 0]
        summary_rows = []
        for p in percentiles:
            q    = p / 100
            invq = 1 - q
            summary_rows.append({
                "Percentile":         f"{p}th percentile",
                "CAR p.a.":           df_stats["CAR"].quantile(q),
                "Volatility p.a.":    df_stats["Vol"].quantile(q),
                "Sharpe Ratio":       df_stats["Sharpe"].quantile(q),
                "Max DD":             df_stats["MaxDD"].quantile(invq),   # <-- inverted
                "95% DD":             df_stats["DD_95"].quantile(invq),   # <-- inverted
            })

        summary = pd.DataFrame(summary_rows).set_index("Percentile")

        # 3) Compute the two custom ratios
        summary["CAR / Max DD"]   = summary["CAR p.a."] / summary["Max DD"]
        summary["CAR / 95% DD"]   = summary["CAR p.a."] / summary["95% DD"]

        # 4) Format all columns for display
        summary = summary.rename(columns={
            "Volatility p.a.": "Volatility p.a.",
            "Sharpe Ratio":    "Sharpe Ratio",
        })

        # percentage‐style
        for col in ["CAR p.a.", "Volatility p.a."]:
            summary[col] = summary[col].map(lambda x: f"{x:.2f}%")
        for col in ["Max DD", "95% DD"]:
            summary[col] = summary[col].map(lambda x: f"-{x:.2f}%")
        summary["Sharpe Ratio"]   = summary["Sharpe Ratio"].map(lambda x: f"{x:.2f}")
        summary["CAR / Max DD"]   = summary["CAR / Max DD"].map(lambda x: f"{x:.2f}")
        summary["CAR / 95% DD"]   = summary["CAR / 95% DD"].map(lambda x: f"{x:.2f}")

        summary.index.name = ""
        summary.columns = [
            "CAR p.a.",
            "Volatility p.a.",
            "Sharpe Ratio",
            "Max DD",
            "95% DD",
            "CAR / Max DD",
            "CAR / 95% DD",
        ]

        # --- NEW: compute $10k terminal values ---
        horizon = T  # horizon input (in years) from the Monte Carlo settings
        # 4A) convert the "%"-strings back to floats
        car_numeric = (
            summary["CAR p.a."]
            .str.replace("%", "", regex=False)
            .astype(float)
            / 100
        )

        # 4B) compute the $10k terminal values
        horizon = T  # your user-input horizon
        terminal_vals = 10_000 * (1 + car_numeric) ** horizon

        # 4C) put them back into the summary dataframe (formatted as dollars)
        summary["Terminal Value (10k)"] = terminal_vals.map(lambda x: f"${x:,.2f}")

        # 5) Display
        st.markdown("**Distribution of Monte Carlo Outcomes (percentile breakdown)**")
        st.table(summary)

        st.markdown("""
            **What this tells us**  
            Because we’ve modeled prices with Geometric Brownian Motion (GBM)—which assumes continuous compounding and normally distributed returns—the simulated outcomes exhibit two drag-and-drop patterns:

            1. **Right-skewed distribution of compounded returns**  
            Over time, the average path drifts upward (thanks to the positive drift term), but the log-normal nature of GBM means a long tail of higher outcomes and a floor that never goes below zero.

            2. **Inverse relation of drawdowns to compounded returns**  
            Higher compound annual returns (CAR) generally coincide with smaller maximum drawdowns, while paths that underperform tend to fall deeper relative to their running peaks.

            Together, these hallmarks reflect how volatility both offers upside optionality and generates downside risk—exactly what you’d expect from a GBM-style model.
            """)


            
    # ----- INTEREST RATES (FRED spreads) -----
    elif chart_choice == "Interest Rates":
        st.subheader("📈 Interest Rate Spreads")
        series_codes = {
            "10Y − 3M Treasury Spread":         "T10Y3M",
            "5Y − Fed Funds Rate Spread":        "T5YFF",
            "TED Spread: 3M LIBOR − 3M T-Bill":  "TEDRATE"
        }
        fred_df = load_fred_series(series_codes, start_date, end_date)

        for name in fred_df.columns:
            fig_ir = px.line(
                fred_df,
                x=fred_df.index,
                y=name,
                title=name,
                labels={name: "Spread (%)"},
                template="plotly_dark",
                width=800,
                height=400
            )
            st.plotly_chart(fig_ir, use_container_width=True)
    else:
        st.subheader("Volatility Indices")

        # 1) Download the three volatility series
        vix = yf.download("^VIX", start=start_date, end=end_date, progress=False)["Close"]
        spx = yf.download("^GSPC", start=start_date, end=end_date, progress=False)["Close"]
        evz = yf.download("^EVZ", start=start_date, end=end_date, progress=False)["Close"]
        gvz = yf.download("^GVZ", start=start_date, end=end_date, progress=False)["Close"]

        # 2) Let the user pick which series to view
        vol_choice = st.radio(
                "Select Volatility Index:",
                ["VIX (Equity)", "EVZ (Euro–Dollar FX)", "GVZ (Gold)"],
                horizontal=True,
                key="portfolio_dashboard_vol_choice"
            )

        if vol_choice == "VIX (Equity)":
            iv_series = vix
            title_iv  = "VIX Index (Equity Market Volatility)"
        elif vol_choice == "EVZ (Euro–Dollar FX)":
            iv_series = evz
            title_iv  = "EVZ Index (30-Day Euro–Dollar FX Implied Vol)"
        else:
            iv_series = gvz
            title_iv  = "GVZ Index (Gold Market Volatility)"

            # 3) Build realized vol & spread only if we have spx + iv_series
        if iv_series.empty or spx.empty:
            st.warning(f"No data available for {vol_choice} in the selected range.")
        else:
            # compute 30-day realized vol (annualized)
            rets = spx.pct_change().dropna()
            rv   = rets.rolling(30).std() * np.sqrt(252)
            rv   = rv * 100


            # align into one DataFrame
            df = pd.concat([iv_series, rv], axis=1).dropna()
            df.columns = ["IV", "RV"]
            df["Spread"]        = df["IV"] - df["RV"]
            df["Spread_1yr_MA"] = df["Spread"].rolling(252).mean()

            # 4) Create a 3-row subplot
            fig = make_subplots(
                    rows=3, cols=1,
                    shared_xaxes=False,
                    vertical_spacing=0.12,
                    subplot_titles=[
                        title_iv,
                        "Daily IV − RV Spread & 1-Yr Rolling Avg",
                        "Distribution of Daily IV − RV Spreads"
                    ]
                )

                # Row 1: IV line
            fig.add_trace(
                    go.Scatter(x=df.index, y=df["IV"], name="IV Level", line=dict(color="cyan")),
                    row=1, col=1
                )

            # Row 2: Spread + rolling average
            fig.add_trace(
                    go.Scatter(x=df.index, y=df["Spread"], name="Daily IV − RV Spread", line=dict(color="cyan")),
                    row=2, col=1
                )
            fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df["Spread_1yr_MA"],
                        name="1-Yr Rolling Avg",
                        line=dict(color="orange", dash="dash")
                    ),
                    row=2, col=1
                )

            # Row 3: Histogram of spreads
            fig.add_trace(
                    go.Histogram(
                        x=df["Spread"],
                        nbinsx=40,
                        opacity=0.8,
                        name="IV − RV Spread",
                        marker_color="lightseagreen"
                    ),
                    row=3, col=1
                )
            # add zero reference line
            fig.add_vline(
                    x=0,
                    line_dash="dash",
                    line_color="white",
                    annotation_text="Zero",
                    annotation_position="top right",
                    row=3, col=1
                )

            # 5) Layout and axis labels
            fig.update_layout(
                    height=1200,
                    template="plotly_dark",
                    margin=dict(t=100, b=60),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )
            # Row 1 labels
            fig.update_yaxes(title_text="IV Level", row=1, col=1)
            # Row 2 labels
            fig.update_yaxes(title_text="Volatility Points", row=2, col=1)
            # Row 3 labels (histogram)
            fig.update_xaxes(title_text="IV − RV (vol points)", row=3, col=1)
            fig.update_yaxes(title_text="Number of Days",      row=3, col=1)

            # 6) Render the chart
            st.plotly_chart(fig, use_container_width=True)
            #st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")
            st.subheader("Volatility Data Table")
            st.dataframe(df)     # or st.table(df) if you prefer a static table



            
elif tab == "Rolling Returns Heatmap":
    st.header("📈 Rolling Daily Average Returns Calendar Heatmap")

    # Create two subtabs: one for VRC, one for Statistical Analysis
    chart_choice = st.radio(
        "Select chart to display:",
        ["VRC", "Momentum Analysis","Reversion Analysis"],
        horizontal=True,
        key="Trend Statistics"
    )
    #vrc_tab, stat_tab = st.tabs(["VRC", "Statistical Analysis"])
    if chart_choice == "VRC":
        # Load & prepare the data exactly as before
        data = load_prices(rolling_ticker, rolling_start_date, rolling_end_date)
        daily_returns = data.pct_change().dropna() * 100

        if daily_returns.empty:
            st.warning("No data to display.")
            st.stop()

        # Build the calendar‐style pivot
        calendar_data = daily_returns.reset_index()
        calendar_data.columns = ['Date', 'Return']
        calendar_data['Year']    = calendar_data['Date'].dt.year
        calendar_data['Month']   = calendar_data['Date'].dt.month
        calendar_data['Day']     = calendar_data['Date'].dt.day
        calendar_data['Week']    = calendar_data['Date'].dt.isocalendar().week
        calendar_data['Weekday'] = calendar_data['Date'].dt.weekday  # 0=Mon…6=Sun

        # Pivot into matrix of weeks × weekdays
        pivot = calendar_data.pivot(index='Week', columns='Weekday', values='Return')

        # Map weekday numbers to names
        weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        pivot.columns = [weekday_labels[d] for d in pivot.columns]

        # Prepare z‐matrix and text annotations
        z = pivot.values
        text = [[f"{val:.2f}" if not pd.isna(val) else "" for val in row] for row in z]

        # Build Plotly heatmap
        import plotly.graph_objects as go
        st.markdown(
            """
            **About this chart:**  
            This calendar‐style heatmap shows the rolling *daily average return* (%) for each 
            Day-of-Week (Mon–Fri) and Week-of-Year over your lookback window.  
            - **Blue** cells = positive returns  
            - **Red** cells = negative returns  
            - **Gray** cells = not enough data  
            """
        )
        fig = go.Figure(
            go.Heatmap(
                z=z,
                x=pivot.columns,
                y=pivot.index.astype(str),
                text=text,
                texttemplate="%{text}",
                colorscale="RdYlBu",
                zmid=0,
                colorbar=dict(title="Return (%)")
            )
        )

        fig.update_layout(
            title=f"Rolling Daily Average Returns\n({rolling_start_date} to {rolling_end_date})",
            xaxis_title="Day of Week",
            yaxis_title="Week Number",
            template="plotly_dark",
            height=600,
            margin=dict(t=80, b=40, l=60, r=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # And still show the raw data table below
        st.subheader("Rolling Returns Data Table")
        st.dataframe(daily_returns)
        st.markdown("""
            #### MarketVision Perspective

            - **Intra-week dynamics:** Observe whether certain weekdays (e.g., mid-week vs. end-week) exhibit persistently higher or lower average returns throughout the selected period.  
            - **Cross-week consistency:** Compare the stability of returns across different week-of-year buckets—some weeks may show reliably elevated performance, while others are more erratic.  
            - **Seasonal signals:** Use the grid to detect calendar effects (quarter-end, month-start, holiday-related flows) that may recur across years.  
            - **Outlier identification:** Highlight cells with unusually large magnitudes to investigate event-driven spikes or drawdowns.  
            - **Data-sufficiency caveat:** Cells rendered in gray reflect limited observations; interpret those areas with discretion.  

            These viewpoints can assist in formulating **entry/exit timing**, **risk controls**, and **deeper event analyses** for any timeframe you choose.
            """)


        st.markdown("---")

        st.header("🌍 Correlation Heatmap")
        st.markdown("""
            **About this chart:**  
            This correlation heatmap illustrates the pairwise Pearson correlation coefficients of daily returns for your selected assets over the chosen period.  

            - **Deep blue cells** indicate a strong positive relationship (ρ → +1).  
            - **Deep red cells** indicate a strong negative relationship (ρ → −1).  
            - **Pale or white cells** indicate little to no linear association (ρ ≈ 0).  

            Below the heatmap, a numeric matrix displays the exact correlation values for precise comparison and further analysis.
            """)

        import yfinance as yf
        import pandas as pd
        import datetime
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # 1) Define tickers and date range
        # 1) Universe of tickers
        universe = ['AAPL','MSFT','AMZN','GOOGL','META','TSLA','NVDA','BRK-B','JPM','V',
                    'JNJ','PG','UNH','HD','BAC','XOM','CVX','PFE','MRK','CSCO',"TQQQ","BTC-USD","TLT",'7203.T','6758.T',                     # Toyota, Sony
            '0700.HK','9988.HK',                   # Tencent, Alibaba HK
            'ASML.AS','SAP.DE','NESN.SW',          # ASML, SAP, Nestlé
            'ULVR.L','HSBA.L','TSM']

        # 2) Sidebar selector (min 3, max 10)
        selected = st.sidebar.multiselect(
            "Select 3–10 stocks for correlation heatmap:",
            options=universe,
            default=universe[:5],
            max_selections=10
        )

        # 3) Enforce minimum
        if len(selected) < 3:
            st.warning("Please select at least 3 stocks to build the heatmap.")
            st.stop()

        # 4) Fetch prices & compute correlation
        today   = datetime.date.today()
        start   = today - datetime.timedelta(days=14)  # ~10 trading days
        prices  = yf.download(selected, start=start, end=today, progress=False)['Close']
        returns = prices.pct_change().dropna()
        corr    = returns.corr()

        # 5) Build Plotly 2-row subplot (heatmap + table)
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.08,
            subplot_titles=["Daily Correlation Matrix", "Correlation Values"],
            specs=[[{"type": "heatmap"}],
                [{"type": "table"}]]
        )

        # 5a) Heatmap
        fig.add_trace(
            go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.index,
                colorscale='RdBu',
                zmin=-1, zmax=1,
                colorbar=dict(title="ρ", len=0.6, y=0.75)
            ),
            row=1, col=1
        )

        # 5b) Table
        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(corr.columns),
                    fill_color='rgba(50,50,50,0.8)',
                    font=dict(color='white', size=12),
                    align='center'
                ),
                cells=dict(
                    values=[corr[col].round(2) for col in corr.columns],
                    fill_color='rgba(30,30,30,0.6)',
                    font=dict(color='white', size=11),
                    align='center'
                )
            ),
            row=2, col=1
        )

        # 6) Layout tweaks & render
        fig.update_layout(
            template='plotly_dark',
            height=700,
            margin=dict(t=80, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
            #### Diversification Guidance

            To construct a portfolio that benefits from negative correlations, consider the following:

            - **Select uncorrelated or inversely correlated assets:** Use the multi-select widget to include securities from different sectors, regions, or asset classes that historically move in opposite directions.  
            - **Adjust your date range:** Broaden or shift the analysis window to capture different market regimes—sometimes negative relationships emerge only in specific environments.  
            - **Increase the universe size:** Including 5–10 instruments improves your chances of finding pairs or groups with strong negative correlations (ρ < 0).  
            - **Monitor rolling windows:** If available, switch to a shorter rolling correlation period (e.g. 30 or 60 days) to emphasise recent dislocations and transient negative relationships.  
            - **Validate with heatmap colors:** Aim for more red cells in the correlation heatmap—this indicates consistently negative pairwise correlations across your chosen timeframe.  

            By iterating these settings, you can identify combinations of assets that are more likely to offset each other’s moves, enhancing risk mitigation and improving portfolio stability.
            """)


    elif chart_choice=="Momentum Analysis":
        st.markdown("---")
        st.header("🔬 Momentum Analysis: Hurst Exponent")
        st.markdown("""
            **Overview:**  
            The Hurst exponent quantifies the persistence or mean-reverting tendency of each selected series over the lookback window.
            """)
        import datetime
        # 1) Allow the user to pick up to 5 symbols
        today   = datetime.date.today()
        start   = today - datetime.timedelta(days=14)  # ~10 trading days
        available = ['AAPL','MSFT','AMZN','GOOGL','META','TSLA','NVDA','BRK-B','JPM','V',
                'GC=F','CL=F','SI=F','NG=F',
                'EURUSD=X','JPY=X','GBPUSD=X','AUDUSD=X']# reuse the same instruments you loaded for correlation
        prices  = yf.download(available, start=start, end=today, progress=False)['Close']
        selected_hurst = st.multiselect(
            "Select 1–5 symbols for Hurst analysis:",
            options=available,
            default=available[:3],
            max_selections=5
        )

        if not selected_hurst:
            st.info("Pick at least one symbol to compute Hurst exponents.")
        else:
            # 2) Fetch a full year of data to ensure >=100 trading days
            end = rolling_end_date
            start = end - pd.Timedelta(days=365)
            price_hist = load_prices(selected_hurst, start, end)

            # 3) Robust Hurst function
            import numpy as np
            from hurst import compute_Hc

            def get_hurst(series, min_len=100):
                s = series.dropna()
                if len(s) < min_len:
                    return np.nan
                try:
                    return compute_Hc(s, kind='price', simplified=False)[0]
                except ValueError:
                    return np.nan

            # 4) Compute and clean up
            hurst_vals = price_hist.apply(get_hurst)
            hurst_vals = hurst_vals.dropna().sort_values()

            if hurst_vals.empty:
                st.warning("Not enough data to compute Hurst for the selected symbols.")
            else:
                # 5) Plot in Plotly
                import plotly.graph_objects as go
                cols = ['grey' if v < 0.55 else 'green' for v in hurst_vals]

                fig_h = go.Figure()
                fig_h.add_trace(go.Bar(
                    x=hurst_vals.index,
                    y=hurst_vals.values,
                    marker_color=cols,
                    hovertemplate="%{x}: %{y:.3f}<extra></extra>"
                ))
                # threshold line
                fig_h.add_shape(type='line',
                                x0=-0.5, x1=len(hurst_vals)-0.5,
                                y0=0.65, y1=0.65,
                                line=dict(color='red', dash='dash'))

                fig_h.update_layout(
                    title="Hurst Exponents (1-Year Lookback)",
                    template="plotly_dark",
                    xaxis_title="Symbol",
                    yaxis_title="Hurst Value",
                    height=450,
                    margin=dict(t=60, b=40, l=40, r=20)
                )
                st.plotly_chart(fig_h, use_container_width=True)  
                st.markdown("""
                    #### Interpretation & Applications

                    - **H > 0.5 (green bars):** Indicates persistent trends—prices tend to continue moving in the same direction.  
                    - **H < 0.5 (gray bars):** Suggests mean‐reversion—prices are more likely to revert toward their long-term average.  
                    - **H ≈ 0.5:** Consistent with a random-walk; no clear trending or reverting behaviour.  

                    The dashed red line marks the threshold (e.g. 0.65) above which we would strongly consider a momentum-driven strategy.  
                    Use these insights to tailor your approach—trend-following when persistence is high, and contrarian strategies when reversion dominates.
                    """)         
        # --- Volatility Bar Chart + Table (Plotly) ---
        st.subheader("📊 Daily Volatility Report")
        st.markdown("""
                **Overview:**  
                This report ranks your selected instruments by their realized daily volatility (%) over the most recent trading day.
                """)

        import datetime, yfinance as yf, pandas as pd
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # 1) Define tickers & date range
        tickers = ['AAPL','MSFT','AMZN','GOOGL','META','TSLA','NVDA','BRK-B','JPM','V']
        today   = datetime.date.today()
        start   = today - datetime.timedelta(days=14)

        # 2) Download OHLC and compute most recent-day volatility
        df      = yf.download(tickers, start=start, end=today, progress=False)
        last    = df.index[-1]
        vols    = {
            t: ((df['High'][t].iloc[-1] - df['Low'][t].iloc[-1]) / df['Open'][t].iloc[-1]) * 100
            for t in tickers
        }
        vol_df  = pd.DataFrame.from_dict(vols, orient='index', columns=['Volatility']).round(4)
        vol_df  = vol_df.sort_values('Volatility', ascending=False).reset_index().rename(columns={'index':'Ticker'})

        # 3) Build Plotly figure: 2 rows (bar + table)
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.6, 0.4],
            vertical_spacing=0.08,
            subplot_titles=[
                f"Daily Volatility for {last.date()}",
                "Volatility Table"
            ],
            specs=[[{"type":"bar"}],
                [{"type":"table"}]]
        )

        # 4a) Bar chart (no text labels above bars)
        fig.add_trace(
            go.Bar(
                x=vol_df['Ticker'],
                y=vol_df['Volatility'],
                marker_color='mediumpurple',
                hovertemplate="%{x}<br>Volatility: %{y:.4f}%",
                showlegend=False
            ),
            row=1, col=1
        )

        # 4b) Table
        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(vol_df.columns),
                    fill_color='rgba(50,50,50,0.8)',
                    font=dict(color='white', size=12),
                    align='center'
                ),
                cells=dict(
                    values=[vol_df[col] for col in vol_df.columns],
                    fill_color=[['#f7d4d4' if v>vol_df['Volatility'].median() else '#d4f7d4' 
                                for v in vol_df['Volatility']],
                                ['rgba(30,30,30,0.6)']*len(vol_df)],  # first column colored, second dark
                    font=dict(color='white', size=11),
                    align='center',
                    format=[None, ".4f"]
                )
            ),
            row=2, col=1
        )

        # 5) Layout tweaks & render
        fig.update_layout(
            template="plotly_dark",
            height=700,
            margin=dict(t=80,b=20,l=40,r=20)
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
                #### Insights & Next Steps

                - **High‐volatility assets** (top of the bar chart) indicate larger price swings—suitable for tactical traders seeking rapid moves but requiring wider risk controls.  
                - **Low‐volatility assets** (bottom of the bar chart) tend to exhibit steadier behavior—often preferred for core portfolio holdings or conservative hedging.  
                - **Volatility clustering:** Compare today’s values to your longer-term averages to spot regimes of elevated or subdued market turbulence.  
                - **Risk management:** Use these metrics to size positions—reduce exposure to instruments exhibiting sudden volatility spikes.  
                - **Diversification:** Combine assets across the volatility spectrum to balance return potential against drawdown risk.  

                Use this volatility report in tandem with your correlation and seasonality analyses to craft a well-balanced, resilient strategy.
                """)

    elif chart_choice == "Reversion Analysis":
        import pandas as pd
        import yfinance as yf
        import statsmodels.tsa.stattools as ts
        import plotly.graph_objects as go

        def adf_gridsearch_multi(tickers,
                                start_date,
                                end_date,
                                window_years=5,
                                step_years=1):
            """
            Runs ADF on each rolling window, returns two DataFrames:
            - pval_df: pivot of actual p-values
            - stat_df: 1 if pval < 0.10 (stationary at 10%), 0 otherwise, NaN if insufficient data
            """
            starts = pd.date_range(start=start_date,
                                end=pd.to_datetime(end_date) - pd.DateOffset(years=window_years),
                                freq=f'{step_years}Y')
            records = []
            for t in tickers:
                for s in starts:
                    e = s + pd.DateOffset(years=window_years)
                    try:
                        series = (yf.download(t, start=s, end=e, progress=False)['Close']
                                    .dropna())
                        if len(series) < 20:
                            pval = None
                        else:
                            pval = ts.adfuller(series)[1]
                    except Exception:
                        pval = None
                    records.append({
                        'ticker': t,
                        'year': s.year,
                        'p_value': pval
                    })
            df = pd.DataFrame(records)
            # pivot
            pval_df = df.pivot(index='ticker', columns='year', values='p_value')
            stat_df = (pval_df < 0.10).astype(float)  # will turn True→1.0, False→0.0, NaN stays NaN
            return pval_df, stat_df

        # --- run it ---
        tickers = ['AUD=X','CAD=X','EUR=X','GBP=X','JPY=X']
        pval_df, stat_df = adf_gridsearch_multi(
            tickers,
            start_date='2006-01-01',
            end_date='2024-12-31'
        )
        # — above the figure —
        st.markdown(
        "**Overview:** This heatmap identifies which FX series exhibit stationarity (ADF p-value < 10%) across rolling 5-year windows."
                    )
        # --- Plotly heatmap ---
        fig = go.Figure(go.Heatmap(
            z=stat_df.values,
            x=stat_df.columns.astype(str),
            y=stat_df.index,
            text=pval_df.round(3).fillna('N/A').values,
            texttemplate='%{text}',
            colorscale=[
                [0.0, 'lightgray'],  # insufficient data or non-stationary
                [0.49, 'lightgray'],
                [0.51, 'green'],     # stationary
                [1.0, 'green']
            ],
            colorbar=dict(
                tickmode='array',
                tickvals=[0,1],
                ticktext=['Not Stationary','Stationary @10%'],
            
            ),
            hovertemplate=
                "<b>%{y}</b><br>" +
                "Window start: %{x}<br>" +
                "p-value: %{text}<extra></extra>"
        ))

        fig.update_layout(
            title={
                'text': "ADF Stationarity Heatmap (5-yr windows, step=1yr)",
                'x': 0.5,             # 0 = left, 0.5 = center, 1 = right
                'xanchor': 'center'   # anchor the title’s x-position at its center
            },
            xaxis_title="Window start year",
            yaxis_title="Ticker",
            yaxis=dict(autorange='reversed'),
            xaxis=dict(tickangle=-45),
            margin=dict(l=100, b=100, t=80),
            width=950,
            height=450,

        )

        #fig.show()
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
            #### Interpretation & Practical Considerations

            - **Stationary windows (green):**  ADF p-value below 0.10 implies the level series has a stable mean and variance over that interval, making it suitable for ARMA‐style modeling without further differencing.  
            - **Non-stationary or insufficient data (gray):**  Either the test failed to reject the unit-root null (p ≥ 0.10) or there were too few observations. In these cases, consider differencing or applying variance-stabilizing transforms.  
            - **Regime sensitivity:**  Stationarity can shift due to macroeconomic changes, policy adjustments, or structural breaks—recompute this heatmap periodically to capture evolving behaviors.  
            - **Strategy design:**  Use persistent green blocks to guide the lookback window for mean-reversion or cointegration strategies. Avoid relying on non-stationary intervals for models that assume constant moments.  
            """)



elif tab == "Return on Equity Heatmap":
    st.header("🏛️ Company Financial Metrics Dashboard")

    # --- Company Selection ---
    largest_30 = [
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'TSLA', 'BRK-B',
        'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC',
        'XOM', 'CMCSA', 'ADBE', 'NFLX', 'VZ', 'INTC', 'T', 'KO', 'PFE',
        'MRK', 'CSCO', 'PEP','ABBV', 'APD', 'ADP', 'CHD', 'CTAS', 'CL', 'KO', 'DOV', 'EXPD',
        'FDS', 'FAST', 'IBM', 'PG', 'ROP', 'TROW', 'MCD', 'PEP', 'SHW',
        'SPGI', 'KMB', 'LIN', 'LOW', 'MKC', 'MDT', 'NDSN', 'NUE', 'PPG',
        'SYY', 'SWK', 'MSFT', 'GOOGL', 'META', 'NFLX', 'MRK', 'UBER',
        'PGR', 'PDD', 'QCOM', 'AMAT', 'LRCX', 'TT', 'NKE', 'ABNB',
        'SCCO', 'CMG', 'ADSK', 'PAYX', 'ROST', 'CMI', 'LULU', 'TPL',
        'ROL', 'TSCO', 'CHKP', 'NVR', 'WAT', 'EME'
    ]

    selected_companies = st.multiselect(
        "Select up to 5 companies to view metrics:",
        largest_30,
        default=["AAPL", "MSFT"],
        max_selections=5
    )

    # --- Toggle Switch ---
    metric_choice = st.radio(
        "Select Metric to View:",
        ["Return on Equity (ROE)", "Debt-to-Equity (D/E)", "Free Cash Flow to Firm (FCFF)", "Company Info"],
        horizontal=True
    )

    # --- Dummy Current Data ---
    dummy_current_roe = {ticker: np.random.randint(10, 45) for ticker in largest_30}
    dummy_current_de = {ticker: np.round(np.random.uniform(0.2, 2.5), 2) for ticker in largest_30}
    dummy_current_fcff = {ticker: np.round(np.random.uniform(10, 100), 2) for ticker in largest_30}  # in billions

    # --- Dummy Historical Data ---
    dummy_historical_roes = {ticker: {year: np.random.randint(10, 45) for year in range(2015, 2023)} for ticker in largest_30}
    dummy_historical_des = {ticker: {year: np.round(np.random.uniform(0.2, 2.5), 2) for year in range(2015, 2023)} for ticker in largest_30}
    dummy_historical_fcffs = {ticker: {year: np.round(np.random.uniform(10, 100), 2) for year in range(2015, 2023)} for ticker in largest_30}

    # === Common function to display metrics + bar chart ===
    def display_metric_and_chart(metric_type, current_data, historical_data, y_label, format_suffix=""):
        st.subheader(f"📋 Current {metric_type}")

        columns = st.columns(len(selected_companies) if selected_companies else 1)

        if selected_companies:
            for idx, company in enumerate(selected_companies):
                with columns[idx]:
                    value = current_data.get(company, "N/A")
                    display_value = f"{value}{format_suffix}" if value != "N/A" else "N/A"
                    st.metric(label=company, value=display_value)
        else:
            st.info("Select at least one company to view data.")

        st.markdown("---")

        st.subheader(f"📊 Historical {metric_type} (Bar Plot)")
        start_year, end_year = st.slider(
            f"Select Year Range for Historical {metric_type}:",
            min_value=2015,
            max_value=2025,
            value=(2015, 2022),
            key=f"{metric_type.replace(' ', '_')}_year_slider"
        )

        if selected_companies:
            years = list(range(start_year, end_year + 1))
            historical_df = pd.DataFrame({ticker: {year: historical_data[ticker].get(year, np.nan) for year in years} for ticker in selected_companies}, index=years)

            if not historical_df.dropna(how="all").empty:
                fig = go.Figure()

                for company in selected_companies:
                    fig.add_trace(go.Bar(
                        x=historical_df.index,
                        y=historical_df[company],
                        name=company,
                        text=historical_df[company],
                        textposition="outside"
                    ))

                fig.update_layout(
                    title=f"Historical {metric_type} Comparison",
                    xaxis_title="Year",
                    yaxis_title=y_label,
                    barmode='group',
                    template="plotly_white",
                    legend_title="Company",
                    width=900,
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Historical {metric_type} data not available.")
        else:
            st.info("Please select companies to display historical data.")
    

    # === Logic based on user toggle choice ===
    if metric_choice == "Return on Equity (ROE)":
        display_metric_and_chart("Return on Equity (ROE)", dummy_current_roe, dummy_historical_roes, "ROE (%)", "%")
    elif metric_choice == "Debt-to-Equity (D/E)":
        display_metric_and_chart("Debt-to-Equity (D/E)", dummy_current_de, dummy_historical_des, "Debt-to-Equity Ratio")
    elif metric_choice == "Free Cash Flow to Firm (FCFF)":
        display_metric_and_chart("Free Cash Flow to Firm (FCFF)", dummy_current_fcff, dummy_historical_fcffs, "Free Cash Flow (Billions USD)", "B")
    else:
        # ————— New Company Information Section —————
        st.subheader("🏢 Company Information")
        st.markdown(
            "Click on each company to learn what they actually do—without scrolling through a boring bullet list!"
        )
        
        selected_companies = st.multiselect(
           "Select up to 5 companies to explore:",
           options=selected_companies,
           default=selected_companies[:2],
           max_selections=5
        )  

        for symbol in selected_companies:
            with st.expander(symbol, expanded=False):
                col1, col2 = st.columns([1, 3])
                with col1:
                    # try to fetch logo + name + summary, but fail gracefully
                    ticker = yf.Ticker(symbol)
                    try:
                        info    = ticker.info
                        name    = info.get("longName", symbol)
                        summary = info.get(
                            "longBusinessSummary",
                            "Summary not available."
                        )
                        logo    = info.get("logo_url", None)
                    except Exception as e:
                        st.warning(f"⚠️ Unable to load data for {symbol}: {e}")
                        name, summary, logo = symbol, "No data.", None

                    if logo:
                        st.image(logo, width=80)
                    else:
                        st.write("🏷️ No logo found")

                with col2:
                    st.markdown(f"### {name}")
                    st.write(summary)
                    wiki_url = f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"
                    st.markdown(f"[🔗 Read more on Wikipedia]({wiki_url})")
                # ————— End Company Information Section —————

    

# --- Tab 4: Strategy Development ---

elif tab == "Strategy Development":
    st.header("🚀 Strategy Development Dashboard")

    # Toggle to Select Strategy View
    strategy_view = st.radio(
        "Select Strategy View:",
        ("Time Series Momentum Strategy", "Buy and Hold Portfolio", "Efficient Frontier Analysis"),
        horizontal=True
    )

    if strategy_view == "Time Series Momentum Strategy":
        st.subheader("📈 Time Series Momentum Strategy")

        #tsmom_ticker = st.sidebar.text_input("Enter ticker for TSMOM:", value="AAPL", key="tsmom_ticker_ts")
        #tsmom_lookback = st.sidebar.slider("Lookback Period (days):", 30, 365, 90, key="lookback_period_ts")
        #tsmom_start_date = st.sidebar.date_input("Start Date for TSMOM:", pd.to_datetime("2022-01-01"), key="tsmom_start_ts")
        #tsmom_end_date = st.sidebar.date_input("End Date for TSMOM:", pd.to_datetime("today"), key="tsmom_end_ts")
        tsmom_ticker = st.sidebar.text_input("Enter ticker for TSMOM", value="AAPL", key="tsmom_ticker")
        tsmom_lookback = st.sidebar.slider("Lookback Period (days)", 30, 365, 90, key="tsmom_lookback")
        tsmom_start = st.sidebar.date_input("Start date", pd.to_datetime("2022-01-01"), key="tsmom_start")
        tsmom_end = st.sidebar.date_input("End date", pd.to_datetime("today"), key="tsmom_end")

        data = yf.download(tsmom_ticker, start=tsmom_start, end=tsmom_end)["Close"]
        if not data.empty:
            returns = data.pct_change().dropna()
            lookback_returns = data.pct_change(periods=tsmom_lookback).shift(1)
            signal = (lookback_returns > 0).astype(int)
            strategy_returns = signal * returns
            cumulative_strategy = (1 + strategy_returns).cumprod()
            cumulative_buy_hold = (1 + returns).cumprod()

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(cumulative_buy_hold, label="Buy & Hold", linestyle="--")
            ax.plot(cumulative_strategy, label="TS Momentum Strategy", linewidth=2)
            ax.set_title(f"TSMOM vs Buy & Hold ({tsmom_ticker})", fontsize=16)
            ax.set_xlabel("Date")
            ax.set_ylabel("Growth of $1 Investment")
            ax.legend()
            st.pyplot(fig)
            plt.close(fig) 
        else:
            st.warning("No price data available for the selected ticker and date range.")
        # ——————————————————————————————————————
        # Commodity Time‐Series Momentum Strategy
        # ——————————————————————————————————————
        st.subheader("📈 TS Momentum Strategy (Commodity)")

        # Let the user pick a commodity
        comm_ticker = st.sidebar.text_input(
            "Enter commodity ticker for TSMOM", 
            value="CL=F", 
            key="tsmom_commodity"
        )

        # Fetch & prepare
        data_comm = yf.download(comm_ticker, start=tsmom_start, end=tsmom_end)["Close"]

        if not data_comm.empty:
            # 1) Returns
            returns_comm     = data_comm.pct_change().dropna()
            # 2) Lookback signal
            lookback_comm    = data_comm.pct_change(periods=tsmom_lookback).shift(1)
            signal_comm      = (lookback_comm > 0).astype(int)
            # 3) Strategy returns
            strat_returns_comm = signal_comm * returns_comm
            # 4) Cumulative paths
            cum_strat_comm     = (1 + strat_returns_comm).cumprod()
            cum_buy_hold_comm  = (1 + returns_comm).cumprod()

            # 5) Plot
            fig_comm, ax_comm = plt.subplots(figsize=(10, 6))
            ax_comm.plot(cum_buy_hold_comm, label="Buy & Hold", linestyle="--")
            ax_comm.plot(cum_strat_comm,    label="TS Momentum Strategy")
            ax_comm.set_title(f"TSMOM vs Buy & Hold ({comm_ticker})", fontsize=16)
            ax_comm.set_xlabel("Date")
            ax_comm.set_ylabel("Growth of $1 Investment")
            ax_comm.legend()
            st.pyplot(fig_comm)
        else:
            st.warning(f"No price data available for {comm_ticker} in the selected date range.")
        # ——————————————————————————————————————
        # Currency Time‐Series Momentum Strategy
        # ——————————————————————————————————————
        st.subheader("📈 TS Momentum Strategy (Currency)")

        # Let the user pick a currency pair
        curr_ticker = st.sidebar.text_input(
            "Enter currency pair ticker for TSMOM",
            value="EURUSD=X",
            key="tsmom_currency"
        )

        # Fetch & prepare
        data_curr = yf.download(curr_ticker, start=tsmom_start, end=tsmom_end)["Close"]

        if not data_curr.empty:
            # 1) Returns
            returns_curr      = data_curr.pct_change().dropna()
            # 2) Lookback signal
            lookback_curr     = data_curr.pct_change(periods=tsmom_lookback).shift(1)
            signal_curr       = (lookback_curr > 0).astype(int)
            # 3) Strategy returns
            strat_returns_curr = signal_curr * returns_curr
            # 4) Cumulative paths
            cum_strat_curr     = (1 + strat_returns_curr).cumprod()
            cum_buy_hold_curr  = (1 + returns_curr).cumprod()

            # 5) Plot
            fig_curr, ax_curr = plt.subplots(figsize=(10, 6))
            ax_curr.plot(cum_buy_hold_curr, label="Buy & Hold", linestyle="--")
            ax_curr.plot(cum_strat_curr,    label="TS Momentum Strategy")
            ax_curr.set_title(f"TSMOM vs Buy & Hold ({curr_ticker})", fontsize=16)
            ax_curr.set_xlabel("Date")
            ax_curr.set_ylabel("Growth of $1 Investment")
            ax_curr.legend()
            st.pyplot(fig_curr)
            plt.close(fig_curr)
        else:
            st.warning(f"No price data available for {curr_ticker} in the selected date range.")

        # ——————————————————————————————————————
        # Treasury Time‐Series Momentum Strategy
        # ——————————————————————————————————————
        st.subheader("📈 TS Momentum Strategy (Treasury Futures)")

        # Let the user pick a treasury futures ticker
        treas_ticker = st.sidebar.text_input(
            "Enter treasury futures ticker for TSMOM",
            value="ZN=F",   # 10-Year Treasury Note Future
            key="tsmom_treasury"
        )

        # Fetch & prepare
        data_treas = yf.download(treas_ticker, start=tsmom_start, end=tsmom_end)["Close"]

        if not data_treas.empty:
            # 1) Returns
            returns_treas      = data_treas.pct_change().dropna()
            # 2) Lookback signal
            lookback_treas     = data_treas.pct_change(periods=tsmom_lookback).shift(1)
            signal_treas       = (lookback_treas > 0).astype(int)
            # 3) Strategy returns
            strat_returns_treas = signal_treas * returns_treas
            # 4) Cumulative paths
            cum_strat_treas     = (1 + strat_returns_treas).cumprod()
            cum_buy_hold_treas  = (1 + returns_treas).cumprod()

            # 5) Plot
            fig_treas, ax_treas = plt.subplots(figsize=(10, 6))
            ax_treas.plot(cum_buy_hold_treas, label="Buy & Hold", linestyle="--")
            ax_treas.plot(cum_strat_treas,    label="TS Momentum Strategy")
            ax_treas.set_title(f"TSMOM vs Buy & Hold ({treas_ticker})", fontsize=16)
            ax_treas.set_xlabel("Date")
            ax_treas.set_ylabel("Growth of $1 Investment")
            ax_treas.legend()
            st.pyplot(fig_treas)
            plt.close(fig_treas)
        else:
            st.warning(f"No price data available for {treas_ticker} in the selected date range.")




    elif strategy_view == "Buy and Hold Portfolio":
        st.subheader("📈 Buy & Hold 10-Stock Portfolio vs SPY")

        portfolio_tickers = st.multiselect(
            "Select 10 stocks for portfolio:",
            [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'UNH',
                'V', 'PG', 'XOM', 'BAC', 'WMT'
            ],
            default=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
            key="portfolio_tickers_bh"
        )

        start_portfolio_date = st.date_input("Portfolio Start Date:", pd.to_datetime("2022-01-01"), key="portfolio_start_bh")
        end_portfolio_date = st.date_input("Portfolio End Date:", pd.to_datetime("today"), key="portfolio_end_bh")

        if len(portfolio_tickers) >= 2:
            prices = yf.download(portfolio_tickers, start=start_portfolio_date, end=end_portfolio_date)["Close"]
            returns = prices.pct_change().dropna()
            equal_weighted_returns = returns.mean(axis=1)

            spy_prices = yf.download("SPY", start=start_portfolio_date, end=end_portfolio_date)["Close"]
            spy_returns = spy_prices.pct_change().dropna()

            cumulative_portfolio = (1 + equal_weighted_returns).cumprod()
            cumulative_spy = (1 + spy_returns).cumprod()

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(cumulative_portfolio, label="10-Stock Portfolio", linewidth=2)
            ax.plot(cumulative_spy, label="SPY Benchmark", linestyle="--")
            ax.set_title("Buy & Hold Portfolio vs SPY", fontsize=16)
            ax.set_xlabel("Date")
            ax.set_ylabel("Growth of $1 Investment")
            ax.legend()
            st.pyplot(fig)
            plt.close(fig) 
        else:
            st.warning("Please select at least 2 stocks for the portfolio.")

        # 1) Sidebar inputs (you can reuse your existing date widgets)
        st.sidebar.subheader("Quality Factor Portfolio")
        q_start = st.sidebar.date_input("Start Date (Quality)", pd.to_datetime("2022-01-01"))
        q_end   = st.sidebar.date_input("End Date (Quality)",   pd.to_datetime("today"))

        portfolio_start = st.date_input("Portfolio Start Date", pd.to_datetime("2022-01-01"),key = "key_management_1")
        portfolio_end   = st.date_input("Portfolio End Date",   pd.to_datetime("today"),key = "key_management_2")
        benchmark_ticker = "QUAL"
        # 2) Define tickers
        quality_universe = [
            "MSFT","GOOGL","META","NFLX","MRK",
            "UBER","PGR", "PDD", "QCOM","AMAT",
            "LRCX","TT","NKE","CTAS","ABNB",
            "SCCO","CMG","ADSK","PAYX","FAST",
            "ROST","CMI","LULU","TPL","ROL",
            "TSCO","CHKP","NVR","WAT","EME"
        ]

        quality_tickers = st.multiselect(
            "Select Quality-Factor stocks for portfolio:",
            quality_universe,
            default=quality_universe[:10],
            help="Pick up to 10 names with high ROE / low debt"
        )

        q_start = st.date_input(
            "Quality Portfolio Start Date",
            value=portfolio_start,
            key="quality_start"
        )
        q_end   = st.date_input(
            "Quality Portfolio End Date",
            value=portfolio_end,
            key="quality_end"
        )


        # 3) Download price data
        data_q = yf.download(quality_tickers + [benchmark_ticker],
                            start=q_start, end=q_end,
                            progress=False)["Close"]

        # 4) Compute daily returns
        rets_q = data_q.pct_change().dropna()
        # equal‐weight portfolio = average of the 10 tickers
        strategy_rets = rets_q[quality_tickers].mean(axis=1)
        bench_rets    = rets_q[benchmark_ticker]

        # 5) Build cumulative growth series
        cum_strategy = (1 + strategy_rets).cumprod()
        cum_bench    = (1 + bench_rets).cumprod()

        # 6) Plot
        st.subheader("📈 Buy & Hold Quality Factor Portfolio vs QUAL")

        fig, ax = plt.subplots(figsize=(12, 6))     # wider figure
        ax.plot(cum_strategy, label="Quality Factor Portfolio", linewidth=2)
        ax.plot(cum_bench,    linestyle="--", label="QUAL Benchmark", linewidth=2)

        # title and labels
        ax.set_title("Buy & Hold Quality Factor Portfolio vs QUAL", pad=15)
        ax.set_xlabel("Date", labelpad=10)
        ax.set_ylabel("Growth of $1", labelpad=10)

        # x-axis ticks every 3 months, rotated for readability
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)

        # subtle grid & tight layout
        ax.grid(which="major", linestyle="--", alpha=0.4)
        ax.legend(loc="upper left", frameon=True)

        fig.tight_layout()
        st.pyplot(fig)

        st.header("📈 Buy & Hold Quality Dividend Portfolio vs SDY")

        # 1) Date inputs (in the sidebar, with unique keys)
        portfolio_start_d = st.date_input("Portfolio Start Date", pd.to_datetime("2022-01-01"), key = "qd_start_1")
        portfolio_end_d   = st.date_input("Portfolio End Date",   pd.to_datetime("today"), key = "qd_end_1")
        st.sidebar.subheader("Quality Dividend Portfolio")
        qd_start = st.sidebar.date_input(
            "Quality Dividend Start Date",
            value=portfolio_start_d,       # reuse your main portfolio_start
            key="qd_start"
        )
        qd_end = st.sidebar.date_input(
            "Quality Dividend End Date",
            value=portfolio_end_d,         # reuse your main portfolio_end
            key="qd_end"
        )

        # 2) Ticker list + benchmark
        quality_dividend_tickers = [
            "ABBV","APD","ADP","CHD",
            "CTAS","CL","KO","DOV","EXPD",
            "FDS","FAST","IBM","PG","ROP",
            "TROW","MCD","PEP","SHW","SPGI",
            "KMB","LIN","LOW","MKC","MDT",
            "NDSN","NUE","PPG","SYY","SWK"
        ]
        benchmark_ticker_d = "SDY"

        
        
        quality_dividend_tickers = st.multiselect(
            "Select Quality-Factor stocks for portfolio:",
            quality_dividend_tickers,
            default=quality_dividend_tickers[:10],
            help="Pick up to 10 names with high ROE / low debt"
        )

        # 3) Download price data
        # 3) Download Adjusted Close prices for dividend universe + SDY
        data_qd = yf.download(
            quality_dividend_tickers + [benchmark_ticker_d],
            start=qd_start, end=qd_end, progress=False
        )["Close"]

        # 4) Compute daily returns off the *right* DataFrame
        rets_qd = data_qd.pct_change().dropna()

        # 5) Filter missing tickers (optional – good practice)
        valid = [t for t in quality_dividend_tickers if t in rets_qd.columns]
        if not valid:
            st.error("No valid tickers loaded; check your selection.")
            st.stop()

        # 6) Calculate strategy vs benchmark returns
        strategy_rets_d = rets_qd[valid].mean(axis=1)
        bench_rets_d    = rets_qd[benchmark_ticker_d]

        # 5) Build cumulative growth series
        cum_strategy_d = (1 + strategy_rets_d).cumprod()
        cum_bench_d    = (1 + bench_rets_d).cumprod()

        # 6) Plot
        st.subheader("📈 Buy & Hold Quality Dividend Factor Portfolio vs QUAL")

        fig, ax = plt.subplots(figsize=(12, 6))     # wider figure
        ax.plot(cum_strategy_d, label="Quality Dividend Factor Portfolio", linewidth=2)
        ax.plot(cum_bench_d,    linestyle="--", label="SDY Benchmark", linewidth=2)

        # title and labels
        ax.set_title("Buy & Hold Quality Dividend Factor Portfolio vs QUAL", pad=15)
        ax.set_xlabel("Date", labelpad=10)
        ax.set_ylabel("Growth of $1", labelpad=10)

        # x-axis ticks every 3 months, rotated for readability
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)

        # subtle grid & tight layout
        ax.grid(which="major", linestyle="--", alpha=0.4)
        ax.legend(loc="upper left", frameon=True)

        fig.tight_layout()
        st.pyplot(fig)


       

        
    elif strategy_view == "Efficient Frontier Analysis":
        import numpy as np
        import pandas as pd
        import streamlit as st
        import yfinance as yf
        import scipy.optimize as sco
        import plotly.graph_objects as go
        import datetime


        st.header("🎯 Efficient Frontier")
        st.markdown("""
            **🚀 Efficient Frontier Explained**  
            The white curve above is the set of _optimal_ portfolios that minimize risk for a given return.  
            - **Min Vol** (★) marks the lowest‐volatility portfolio.  
            - **Max Sharpe** (★) marks the portfolio with the highest reward‐to‐risk ratio.  
            - The red dashed line is the Capital Market Line: combining the risk-free asset with the market portfolio yields the best attainable risk/return tradeoff.
            """)

        # --- Define 50 largest S&P500 stocks ---
        # 1) Universe of tickers (e.g. top 50 S&P)
        universe =  [
        'ABBV', 'APD', 'ADP', 'CHD', 'CTAS', 'CL', 'KO', 'DOV', 'EXPD',
        'FDS', 'FAST', 'IBM', 'PG', 'ROP', 'TROW', 'MCD', 'PEP', 'SHW',
        'SPGI', 'KMB', 'LIN', 'LOW', 'MKC', 'MDT', 'NDSN', 'NUE', 'PPG',
        'SYY', 'SWK', 'MSFT', 'GOOGL', 'META', 'NFLX', 'MRK', 'UBER',
        'PGR', 'PDD', 'QCOM', 'AMAT', 'LRCX', 'TT', 'NKE', 'ABNB',
        'SCCO', 'CMG', 'ADSK', 'PAYX', 'ROST', 'CMI', 'LULU', 'TPL',
        'ROL', 'TSCO', 'CHKP', 'NVR', 'WAT', 'EME'
        ]


        # 2) Sidebar selector with minimum 3, maximum 10
        selected = st.sidebar.multiselect(
            "Select 9 stocks for your efficient frontier:",
            options=universe,
            default=universe[:9],
            max_selections=20
        )

        # 3) Enforce minimum
        if len(selected) < 9:
            st.warning("Please select at least 3 stocks to build the efficient frontier.")
            st.stop()

        # 4) Download & prepare returns
        today = datetime.date.today()
        start = "2000-01-01"
        prices = yf.download(selected, start=start, end=today, progress=False)["Close"]
        returns = prices.pct_change().dropna()

        mean_returns = returns.mean() * 252
        cov_matrix   = returns.cov()  * 252
        rf_rate      = 0.02

        # 5) Efficient frontier calculation
        def portfolio_perf(w):
            r = np.dot(mean_returns, w)
            v = np.sqrt(w @ cov_matrix @ w)
            return r, v

        def min_vol_for_ret(target):
            n = len(mean_returns)
            init = np.repeat(1/n, n)
            bounds = [(0,1)]*n
            cons   = (
                {"type":"eq","fun": lambda w: np.sum(w)-1},
                {"type":"eq","fun": lambda w: portfolio_perf(w)[0]-target}
            )
            sol = sco.minimize(lambda w: portfolio_perf(w)[1], init,
                            method="SLSQP", bounds=bounds, constraints=cons)
            return sol.fun if sol.success else np.nan

        rets = np.linspace(mean_returns.min(), mean_returns.max(), 100)
        vols = [min_vol_for_ret(r) for r in rets]

        # 6) CML, max‐Sharpe & min‐vol points
        # Max Sharpe
        def neg_sharpe(w):
            r,v = portfolio_perf(w)
            return -(r - rf_rate)/v

        n = len(mean_returns)
        init = np.repeat(1/n, n)
        bounds = [(0,1)]*n
        cons   = ({"type":"eq","fun": lambda w: np.sum(w)-1},)
        sh = sco.minimize(neg_sharpe, init, method="SLSQP", bounds=bounds, constraints=cons)
        r_sh,v_sh = portfolio_perf(sh.x)

        # Min vol
        mv = sco.minimize(lambda w: portfolio_perf(w)[1], init,
                        method="SLSQP", bounds=bounds, constraints=cons)
        r_mv,v_mv = portfolio_perf(mv.x)

        # 7) Build Plotly subplots: frontier (row 1) + table (row 2)
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.65, 0.35],
            vertical_spacing=0.15,
            subplot_titles=["Efficient Frontier", "Frontier Data"],
            specs=[[{"type":"scatter"}], [{"type":"table"}]]
        )

        # 7a) Efficient frontier line
        fig.add_trace(
            go.Scatter(x=vols, y=rets, mode="lines",
                    line=dict(color="white", width=2),
                    name="Frontier"),
            row=1, col=1
        )

        # 7b) Capital Market Line
        cml_x = np.linspace(0, max(vols), 100)
        cml_y = rf_rate + ((r_sh - rf_rate)/v_sh)*cml_x
        fig.add_trace(
            go.Scatter(x=cml_x, y=cml_y, mode="lines",
                    line=dict(color="red", dash="dot"),
                    name="CML"),
            row=1, col=1
        )

        # 7c) Max Sharpe & Min Vol points
        fig.add_trace(
            go.Scatter(x=[v_sh], y=[r_sh], mode="markers+text",
                    marker=dict(color="blue", size=10, symbol="star"),
                    text=["Max Sharpe"], textposition="top center",
                    name="Max Sharpe"),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=[v_mv], y=[r_mv], mode="markers+text",
                    marker=dict(color="green", size=10, symbol="star"),
                    text=["Min Vol"], textposition="bottom center",
                    name="Min Volatility"),
            row=1, col=1
        )

        # 7d) Individual stocks
        ind_vols = returns.std()*np.sqrt(252)
        ind_rets = mean_returns
        fig.add_trace(
            go.Scatter(x=ind_vols, y=ind_rets, mode="markers",
                    marker=dict(color="lime", size=7),
                    text=ind_vols.index,
                    hovertemplate="<b>%{text}</b><br>Vol: %{x:.2%}<br>Ret: %{y:.2%}",
                    name="Stocks"),
            row=1, col=1
        )

        # 7e) Table of frontier values
        table_df = pd.DataFrame({
            "Volatility": vols,
            "Return":     rets
        }).round(4)
        fig.add_trace(
            go.Table(
                header=dict(values=["Volatility", "Return"],
                            fill_color="lightgrey", align="center"),
                cells=dict(values=[table_df["Volatility"], table_df["Return"]],
                        align="center", format=[".4f", ".4f"])
            ),
            row=2, col=1
        )

        # 8) Layout & render
        fig.update_layout(
            template="plotly_dark",
            height=700,
            margin=dict(t=80, b=20, l=20, r=20),
            xaxis_title="Risk (Volatility)",
            yaxis_title="Return",
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.1,                          # ↑ pull legend further into that new margin
                yanchor="top",
                font=dict(size=12)               # (optional) shrink text for extra breathing room
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""
            **🔧 How to Use This Table**  
            1. **Select a target volatility** (left column) based on your risk budget.  
            2. **Read off the matching expected return** (right column).  
            3. **Plug these targets** into your portfolio optimizer or backtest as your risk/return objective.  
            4. **Shift along the curve** for more aggressive (higher vol) or conservative (lower vol) allocations.  
            """)

        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import streamlit as st

        # --- assume you already have `returns_df` (daily pct-change of each asset),
        #     and you’ve computed `frontier_vols`, `frontier_rets`

        def simulate_random_portfolios(returns, n_sims=3000):
            mean_rets = returns.mean() * 252
            cov       = returns.cov() * 252
            n_assets  = len(mean_rets)

            sims = np.random.rand(n_sims, n_assets)
            sims /= sims.sum(axis=1)[:, None]            # normalize to weights sum = 1

            port_vols = []
            port_rets = []

            for w in sims:
                port_rets.append(w.dot(mean_rets))
                port_vols.append(np.sqrt(w.T.dot(cov).dot(w)))

            return np.array(port_vols), np.array(port_rets)
        
        # after you've built your `returns` DataFrame...
        sim_vols, sim_rets = simulate_random_portfolios(returns, n_sims=3000)


        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10,6))

        # 1) Build KDE over the random portfolios
        xy = np.vstack([sim_vols, sim_rets])
        z  = gaussian_kde(xy)(xy)
        idx = z.argsort()

        # 2) Plot the density‐coloured random cloud
        ax.scatter(sim_vols[idx], sim_rets[idx],
                c=z[idx], cmap='viridis', s=20, alpha=0.6,
                marker='o', label='Random Portfolios', zorder=1)

        # 3) Plot the efficient frontier on top
        ax.plot(vols, rets,
                linewidth=3, linestyle='-',
                label='Efficient Frontier', zorder=3)

        # 4) Highlight Min Vol & Max Sharpe
        ax.scatter([v_mv], [r_mv], s=150, marker='*',
                edgecolors='w', linewidths=1.5,
                label='Min Vol', zorder=4)
        ax.scatter([v_sh], [r_sh], s=150, marker='*',
                edgecolors='w', linewidths=1.5,
                label='Max Sharpe', zorder=4)
        ax.text(v_mv, r_mv, '  Min Vol', va='bottom', ha='left')
        ax.text(v_sh, r_sh, '  Max Sharpe', va='bottom', ha='left')

        # 5) Tidy up
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)
        ax.set_xlabel("Risk (Volatility)", fontsize=12)
        ax.set_ylabel("Return", fontsize=12)
        ax.set_title("Efficient Frontier vs. Random Portfolios", fontsize=14)
        ax.legend(loc='upper left', fontsize=10, frameon=False)

        #plt.tight_layout()
        #plt.show()
        # … after ax.legend() etc.
        plt.tight_layout()

        # (remove plt.show())

        # Send it to Streamlit:
        st.pyplot(fig)

        # 8) Asset Correlation Heatmap
        st.subheader("🔗 Asset Correlation Heatmap")
        st.markdown("""
        A heatmap of your assets’ return correlations.  
        Pairs with **low correlations** (blue) are the ones driving the outward bend of your frontier.
        """)

        # compute the correlation matrix
        corr = returns.corr()

        # build a Plotly heatmap
        fig_corr = go.Figure(
            data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.index,
                colorscale="RdBu",   # blue ↔ red diverging
                zmid=0,              # center the colormap at zero
                colorbar=dict(title="Correlation")
            )
        )
        fig_corr.update_layout(
            template="plotly_dark",
            height=600,
            margin=dict(t=40, l=40, r=40, b=40)
        )

        # render in Streamlit
        st.plotly_chart(fig_corr, use_container_width=True)

        # 9) Portfolio Weights Bar Chart (Min-Vol & Max-Sharpe)
        st.subheader("📊 Portfolio Weights: Min Vol vs. Max Sharpe")
        st.markdown("""
        Horizontal bar chart showing the asset weights in your two optimal portfolios:
        - **Min Vol** portfolio  
        - **Max Sharpe** portfolio  
        """)


        # pack the weight arrays into a DataFrame
        w_min    = mv.x                 # from your min-vol optimizer
        w_sharpe = sh.x                 # from your max-sharpe optimizer
        assets   = returns.columns      # or your `selected` tickers list

        weights_df = pd.DataFrame(
            [w_min, w_sharpe],
            index=["Min Vol", "Max Sharpe"],
            columns=assets
        )

        # transpose so each asset is a bar group
        st.bar_chart(weights_df.T)

        # 10) Rolling Value-at-Risk (VaR) Over Time
        st.subheader("🛡️ Rolling Value-at-Risk (VaR)")
        st.markdown("""
        A time-series of your **Max Sharpe** portfolio’s rolling 95% VaR, using a 252-day window.  
        This shows the worst expected daily loss (at 95% confidence) under normal market conditions.
        """)

        # 1) Compute portfolio returns for the Max-Sharpe weights
        #    (you already solved: sh = sco.minimize(…); r_sh, v_sh = portfolio_perf(sh.x))
        port_rets = returns.dot(sh.x)

        # 2) Compute the 95% rolling VaR (5th percentile of daily returns)
        rolling_var = port_rets.rolling(window=252).quantile(0.05)

        # 3) Plot with Plotly
        fig_var = go.Figure()
        fig_var.add_trace(
            go.Scatter(
                x=rolling_var.index,
                y=rolling_var,
                mode="lines",
                line=dict(color="cyan"),
                name="95% VaR"
            )
        )
        fig_var.update_layout(
            template="plotly_dark",
            height=500,
            margin=dict(t=40, b=40, l=40, r=40),
            xaxis_title="Date",
            yaxis_title="Daily VaR (loss)",
            yaxis_tickformat=".2%",
        )
        st.plotly_chart(fig_var, use_container_width=True)
