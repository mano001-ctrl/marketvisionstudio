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
    ["Asset Snapshot", "Statistical Insights", "Corporate Metrics Hub", "Strategy Development"]
)

# --- Sidebar (dynamic) ---
if tab == "Asset Snapshot":
    #st.header("Rudimental Asset Info")

    # --- Sidebar Settings ---
    st.sidebar.header("Settings: Asset Snapshot")
    # 1) Stocks
    stock_list = ['AAPL','MSFT','GOOGL','AMZN','TSLA','META','NVDA','JPM','JNJ','V','TQQQ'] 
    selected_stocks = st.sidebar.multiselect(
        "Select Stocks:",
        stock_list,
        default=['AAPL','MSFT'],
        key="portfolio_stocks"
    )
    

    # --- Date Range ---
    start_date = st.sidebar.date_input("Start date", pd.to_datetime("2017-01-01"), key="first_portfolio_start")
    end_date   = st.sidebar.date_input("End date",   pd.to_datetime("today"),    key="first_portfolio_end")

    # Combine all instruments
    instruments = selected_stocks 

    if not instruments:
        st.info("Please select at least one instrument to display charts.")
        st.stop()


elif tab == "Statistical Insights":
    st.sidebar.header("Settings: Rolling Daily Average Returns")
    rolling_ticker = st.sidebar.text_input("Ticker for rolling heatmap", value="SPY", key="heatmap_ticker")
    rolling_start_date = st.sidebar.date_input("Start date", pd.to_datetime("today") - pd.Timedelta(days=30), key="heatmap_start")
    rolling_end_date = st.sidebar.date_input("End date", pd.to_datetime("today"), key="heatmap_end")

    st.sidebar.header("Settings: Daily Correlation Matrix")
    sector_start = st.sidebar.date_input("Start date for sector heatmap", pd.to_datetime("today") - pd.Timedelta(days=60), key="sector_start")
    sector_end = st.sidebar.date_input("End date for sector heatmap", pd.to_datetime("today"), key="sector_end")

elif tab == "Corporate Metrics Hub":
    st.sidebar.header("No settings required for ROE Heatmap.")

elif tab == "Strategy Development":
    st.sidebar.header("Settings: Strategy Development")


# --- Main Area Content ---
# --- Main Area Content ---
if tab == "Asset Snapshot":
    st.header("Rudimental Asset Information")

    if not selected_stocks:
        st.info("Please select at least one stock to display charts.")
        st.stop()

    # Load price & returns
    prices        = load_prices(instruments, start_date, end_date)
    daily_returns = prices.pct_change().dropna()

    # Chart selector
    chart_choice = st.radio(
        "Select chart to display:",
        ["Price Data", "Interest Rates", "Volatility"],
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
        for ticker in prices.columns:
            fig.add_trace(go.Scatter(
                x=prices.index,
                y=prices[ticker],
                name=ticker,
                yaxis='y'
            ))

        fig.update_layout(
            template='plotly_dark',
            yaxis=dict(title='Price'),
            legend=dict(
                orientation='h',
                x=0.5, xanchor='center',
                y=-0.2, yanchor='top'
            )
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
        st.subheader("Interest Rate Spreads")
        st.markdown(
        """
        **What are Interest Rate Spreads?**  
        An interest rate spread is the difference between two yield rates—typically
        a long-term government bond minus a short-term rate.  
        
        - **10Y − 3M Treasury Spread (T10Y3M):** A classic recession signal: when
          short-term rates exceed long-term (i.e. an inverted curve), economic
          growth often slows.  
        - **5Y − Fed Funds Spread (T5YFF):** Shows how market expectations for
          Fed policy diverge from today’s overnight rate.  
        - **TED Spread:** The gap between 3-month LIBOR and 3-month T-bill, a
          gauge of banking-sector stress.
        """
        )
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
        st.subheader("Volatility")

        st.markdown(
        """
        **What are Volatility Indices?**  
        A volatility index shows the market’s expectation of future volatility, as implied by option prices:

        - **VIX (Equity):** Often called the “fear gauge,” it’s derived from S&P 500 option prices and reflects expected 30-day equity volatility.  
        - **EVZ (Euro–Dollar FX):** Measures 30-day implied volatility on EUR/USD options—useful for currency risk.  
        - **GVZ (Gold):** Tracks 30-day implied volatility in gold futures options, a barometer of precious-metal market stress.
        """
        )

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

            
            st.markdown("---")
            st.subheader("Implied Volatility Surface (Market Volatility Example)")
            import numpy as np
            import plotly.graph_objects as go

            # 1. Define strike and maturity ranges
            strikes = [600, 610, 620, 630, 640]
            maturities = [1/12, 3/12, 6/12, 1, 2]  # in years

            # 2. Volatility matrix (%)
            vols = np.array([
                [28.0, 24.5, 22.0, 20.5, 19.5],
                [27.5, 24.0, 21.8, 20.3, 19.3],
                [27.0, 23.5, 21.5, 20.0, 19.0],
                [26.5, 23.0, 21.2, 19.8, 18.8],
                [26.0, 22.5, 21.0, 19.5, 18.5]
            ])

            # 3. Create mesh grid
            X, Y = np.meshgrid(strikes, maturities)

            # 4. Build 3D surface
            fig_vol_surface = go.Figure(data=[go.Surface(
                x=X, y=Y, z=vols,
                colorscale='viridis'
            )])

            # 5. Layout settings
            fig_vol_surface.update_layout(
                title='Implied Volatility Surface',
                scene=dict(
                    xaxis_title='Strike Price',
                    yaxis_title='Time to Maturity (Years)',
                    zaxis_title='Implied Volatility (%)',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                width=800,
                height=600,
                template='plotly_dark',
                paper_bgcolor='rgb(30,30,30)',
                plot_bgcolor='rgb(30,30,30)'
            )

            st.plotly_chart(fig_vol_surface, use_container_width=True)

            import streamlit as st
            import numpy as np
            import plotly.graph_objects as go

            # Section heading
            st.markdown("---")
            st.subheader("Black-Scholes Volatility Surface (Static Example)")

            # Data setup
            strikes = [90, 95, 100, 105, 110]
            maturities = [1/12, 3/12, 6/12, 1, 2]
            market_vols = np.array([
                [28.0, 24.5, 22.0, 20.5, 19.5],
                [27.5, 24.0, 21.8, 20.3, 19.3],
                [27.0, 23.5, 21.5, 20.0, 19.0],
                [26.5, 23.0, 21.2, 19.8, 18.8],
                [26.0, 22.5, 21.0, 19.5, 18.5]
            ])
            X, Y = np.meshgrid(strikes, maturities)

            # Set previous vol and current BS vol
            previous_vol = 20.0
            bs_vol = 22.0

            previous_vol_surface = np.full_like(market_vols, previous_vol)
            current_vol_surface = np.full_like(market_vols, bs_vol)

            # Create static plot with both surfaces
            fig_static = go.Figure(data=[
                go.Surface(x=X, y=Y, z=previous_vol_surface, colorscale='Reds', opacity=0.3, showscale=False),
                go.Surface(x=X, y=Y, z=current_vol_surface, colorscale='Blues', opacity=0.7, showscale=False)
            ])

            # Layout configuration
            fig_static.update_layout(
                title='Black-Scholes Volatility Surface (Static)',
                scene=dict(
                    xaxis_title='Strike Price',
                    yaxis_title='Time to Maturity (Years)',
                    zaxis_title='Implied Volatility (%)',
                    zaxis=dict(range=[18, 25]),
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
                ),
                width=900,
                height=600,
                template='plotly_dark',
                paper_bgcolor='rgb(30,30,30)',
                plot_bgcolor='rgb(30,30,30)'
            )

            # Display in Streamlit
            st.plotly_chart(fig_static, use_container_width=True)

            st.markdown("""
            ### Comparing Black-Scholes vs Market-Implied Volatility Surfaces
            
            The implied volatility surface is more than a mathematical construct — it reflects actual trader behavior, risk perception, and market mechanics. The contrast between theoretical and market surfaces highlights the gap between assumption and reality.
            
            ---
            
            #### Black-Scholes Volatility Surface (Static Assumption)
            - Assumes **constant volatility** across all strikes and maturities.
            - The surface is **flat and featureless**, as seen in the static 3D plot.
            - Ignores structural realities like **volatility smiles**, **skews**, and **term structure**.
            - Useful for foundational theory, but **poor at capturing market nuances**.
            
            ---
            
            #### Market-Implied Volatility Surface (Empirical Observation)
            - Derived from real option prices, showing how **volatility varies** by strike and maturity.
            - Displays **skew** (higher IV for OTM puts), **term structure** (longer-dated options often pricier), and **smile effects**.
            - Reflects **supply-demand dynamics**, **risk aversion**, and **hedging pressures**.
            - This is the volatility that **traders use for pricing, hedging, and strategy design**.
            
            ---
            
            #### Why the Discrepancy Matters
            - Black-Scholes assumes the world is smooth — but markets are jagged.
            - Market-implied volatility captures **trader fear, positioning, and structural demand**.
            - Trading strategies like **volatility arbitrage**, **delta-hedging**, and **tail-risk hedging** all rely on the **empirical surface**, not the flat Black-Scholes one.
            
            ---
            
            #### Practical Implication for Traders
            - Using the Black-Scholes model in isolation can lead to **underestimating risk** and **mispricing options**.
            - Most traders rely on **implied volatility surfaces from market data providers**, not theoretical models.
            - **Sophisticated models** (e.g., SABR, Heston) attempt to fit the real-world surface better than Black-Scholes.
            
            ---
            
            **Final Remarks**:  
            The Black-Scholes surface may look clean — but it’s an illusion.  
            The **market-implied surface is messy, asymmetric, and reactive** — but it’s real.  
            For anyone trading options seriously, **understanding this surface is critical** to navigating risk, pricing, and performance.
            
            """)


            import streamlit as st
            import numpy as np
            import plotly.graph_objects as go
            from scipy.stats import norm

            # Section heading
            st.markdown("---")
            st.subheader("Heston Implied Volatility Surface (Static Example)")

            # 1. Market Data
            strikes = [90, 95, 100, 105, 110]
            maturities = [1/12, 3/12, 6/12, 1, 2]
            market_vols = np.array([
                [28.0, 24.5, 22.0, 20.5, 19.5],
                [27.5, 24.0, 21.8, 20.3, 19.3],
                [27.0, 23.5, 21.5, 20.0, 19.0],
                [26.5, 23.0, 21.2, 19.8, 18.8],
                [26.0, 22.5, 21.0, 19.5, 18.5]
            ])
            X, Y = np.meshgrid(strikes, maturities)

            # 2. Heston Model Simulation
            def heston_paths(S0, v0, kappa, theta, xi, rho, r, T, N, M):
                dt = T / N
                S = np.zeros((N + 1, M))
                v = np.zeros((N + 1, M))
                S[0] = S0
                v[0] = v0
                Z1 = np.random.standard_normal((N, M))
                Z2 = rho * Z1 + np.sqrt(1 - rho ** 2) * np.random.standard_normal((N, M))
                for i in range(N):
                    v[i + 1] = np.maximum(v[i] + kappa * (theta - v[i]) * dt + xi * np.sqrt(np.maximum(v[i], 0) * dt) * Z1[i], 0)
                    S[i + 1] = S[i] * np.exp((r - 0.5 * v[i]) * dt + np.sqrt(np.maximum(v[i], 0) * dt) * Z2[i])
                return S, v

            def bs_implied_vol(S0, K, T, r, price, call=True):
                def bs_price(sigma):
                    d1 = (np.log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
                    d2 = d1 - sigma * np.sqrt(T)
                    return S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2) if call else K * np.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)
                
                sigma = 0.3
                for _ in range(100):
                    price_diff = bs_price(sigma) - price
                    if abs(price_diff) < 1e-5:
                        return sigma
                    d1 = (np.log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
                    vega = S0 * np.sqrt(T) * norm.pdf(d1)
                    if vega == 0:
                        return sigma
                    sigma -= price_diff / vega
                    sigma = max(sigma, 0.01)
                return sigma

            # 3. Model Parameters
            S0 = 100
            v0 = 5.208 / 100  # Initial variance as decimal
            kappa = 2.0
            theta = 0.04
            xi = 0.3
            rho = -0.7
            r = 0.02
            N_paths = 100000

            # 4. Compute Heston Implied Vols
            heston_vols = np.zeros_like(market_vols)
            for i, T in enumerate(maturities):
                N_steps = max(int(T * 252), 1)
                for j, K in enumerate(strikes):
                    S, v = heston_paths(S0, v0, kappa, theta, xi, rho, r, T, N_steps, N_paths)
                    payoffs = np.maximum(S[-1] - K, 0)
                    price = np.exp(-r * T) * np.mean(payoffs)
                    try:
                        heston_vols[i, j] = bs_implied_vol(S0, K, T, r, price) * 100
                    except:
                        heston_vols[i, j] = np.nan

            # 5. Create and display the 3D Heston surface in Streamlit
            fig_heston = go.Figure(data=[
                go.Surface(x=X, y=Y, z=heston_vols, colorscale='Viridis', opacity=0.85, showscale=True)
            ])

            fig_heston.update_layout(
                title='Heston Implied Volatility Surface',
                scene=dict(
                    xaxis_title='Strike Price',
                    yaxis_title='Time to Maturity (Years)',
                    zaxis_title='Implied Volatility (%)',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
                    bgcolor='rgb(30,30,30)'
                ),
                width=950,
                height=600,
                template='plotly_dark',
                paper_bgcolor='rgb(30,30,30)',
                plot_bgcolor='rgb(30,30,30)'
            )

            st.plotly_chart(fig_heston, use_container_width=True)




           


            st.markdown("""
                 ### Interpreting the Implied Volatility Surface: Risk, Behavior, and Regulation  
                
                 This 3D surface shows how **implied volatility** changes with respect to **strike price** and **time to maturity**. But beyond the surface lies a rich ecosystem of pricing anomalies and behavioral drivers:
                
                 ---
                
                 #### Variance Premium  
                 - **Implied volatility (IV)** systematically exceeds **realized volatility (RV)** — this difference is the **variance risk premium (VRP)**.  
                 - Investors pay a premium for protection against volatility spikes, which creates an opportunity for sellers to earn this premium consistently.  
                 - This VRP is embedded in option prices — especially in short-dated, out-of-the-money (OTM) puts — and steepens the skew you see in the surface.
                
                 ---
                
                 #### Straddle Strategy and Surface Interpretation  
                 - A **straddle** involves buying or selling both a call and a put at the same strike — typically at-the-money (ATM).  
                 - The notebook's example shows that **selling straddles** profits when actual volatility is less than implied — i.e., harvesting the **variance premium**.  
                 - These strategies implicitly short the volatility surface, profiting from mean-reverting vol but exposing the trader to tail events.
                
                 ---
                
                 #### Loss Aversion and Overpriced Tails  
                 - As per **Prospect Theory**, investors **dislike losses more than they like gains**.  
                 - This behavioral trait causes **deep OTM puts to be overpriced**, leading to a skewed surface (higher IV for lower strikes).  
                 - Loss-averse institutions **overpay for insurance** — skewing demand and elevating tail prices.
                
                 ---
                
                 #### Regulatory Demand for Tail Protection  
                 - Financial institutions (banks, insurers, pensions) **must hedge tail risk** to meet regulatory requirements like **Basel III**, **Solvency II**, or **FRTB**.  
                 - **Tail hedges reduce capital charges** and improve solvency/funding ratios by shaping the loss distribution.  
                 - This creates a **structural, persistent bid** for tail protection, further inflating implied vol in the left tail.
                
                 ---
                
                 **Final Remarks**:  
                 The implied volatility surface is not just a pricing map — it’s a reflection of **fear, regulation, and systemic behavior**.  
                 The steepness of the surface and the richness of the premium available are a result of:  
                 - Investors' **fear of rare losses (loss aversion)**  
                 - Institutions’ **need to survive under regulatory scrutiny**  
                 - And the **persistent overpricing of crash insurance**, which option sellers aim to monetize — carefully.
                """)



            
elif tab == "Statistical Insights":
    st.header("Rolling Daily Average Returns")

    # Create two subtabs: one for VRC, one for Statistical Analysis
    chart_choice = st.radio(
        "Select chart to display:",
        ["Returns & Correlation", "Momentum Analysis","CAPM"],
        horizontal=True,
        key="Trend Statistics"
    )
    #vrc_tab, stat_tab = st.tabs(["VRC", "Statistical Analysis"])
    if chart_choice == "Returns & Correlation":
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

    else:
        # file: statistical_insights.py

        import streamlit as st
        import yfinance as yf
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go

        @st.cache_data(ttl=3600)
        def load_returns(market_symbol: str, portfolio_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
            prices = yf.download([market_symbol, portfolio_symbol],
                                start=start_date, end=end_date)['Close']
            returns = prices.pct_change().dropna()
            returns.columns = ['market_returns', 'portfolio_returns']
            return returns

        def capm_vs_regression_widget():
            st.subheader("CAPM β vs OLS Regression (Best viewed in Full Screen Mode)")
            st.markdown("""
            **What is CAPM?**  
            The Capital Asset Pricing Model (CAPM) describes the relationship between systematic risk (beta, β) and expected return.  
            - **β (beta):** Measures how sensitively your stock’s returns move with the overall market.  
            - β > 1 → more volatile than the market  
            - β < 1 → less volatile than the market  
            - β = 1 → moves in lock-step with the market  
            - **OLS Regression:** Ordinary Least Squares line fit to your stock’s daily returns vs. market returns.  

            **How to interpret this chart:**  
            1. **Slope of the green line (CAPM β):** Your stock’s “fair” compensation per unit of market risk.  
            2. **Dashed purple line (OLS fit):** Empirical regression–based estimate of β and the intercept (α).  
            3. **Scatter points:** Each point is one day’s pair of (market return, stock return).  

            —  
            """)

            # --- Inputs ---
            col1, col2 = st.columns(2)
            with col1:
                market_symbol = st.text_input("Market index ticker", "^GSPC")
                portfolio_symbol = st.text_input("Portfolio ticker", "AAPL")
            with col2:
                start_date = st.date_input("Start date", pd.to_datetime("2015-01-01"))
                end_date   = st.date_input("End date",   pd.to_datetime("2020-01-01"))

            if st.button("Update Chart"):
                # 1) Load & align returns
                df = load_returns(market_symbol, portfolio_symbol, start_date, end_date)

                # 2) Compute CAPM β
                cov_xy    = df['market_returns'].cov(df['portfolio_returns'])
                var_x     = df['market_returns'].var()
                beta_capm = cov_xy / var_x

                # 3) Fit OLS regression
                slope, intercept = np.polyfit(df['market_returns'], df['portfolio_returns'], 1)

                # 4) Prepare lines
                x_vals = np.linspace(df['market_returns'].min(), df['market_returns'].max(), 100)
                y_capm = beta_capm * x_vals
                y_reg  = intercept + slope * x_vals

                # 5) Build Plotly figure
                fig = go.Figure([
                    go.Scatter(
                        x=df['market_returns'], y=df['portfolio_returns'],
                        mode='markers', name='Data',
                        marker=dict(size=6, opacity=0.7, line=dict(width=0.5, color='DarkSlateGrey'))
                    ),
                    go.Scatter(
                        x=x_vals, y=y_capm, mode='lines',
                        name=f'CAPM β line (β={beta_capm:.2f})',
                        line=dict(color='green', width=2)
                    ),
                    go.Scatter(
                        x=x_vals, y=y_reg, mode='lines',
                        name=f'OLS line (slope={slope:.2f}, α={intercept:.4f})',
                        line=dict(color='purple', width=2, dash='dash')
                    )
                ])
                fig.update_layout(
                    template='plotly_white',
                    xaxis_title='Market Returns',
                    yaxis_title='Portfolio Returns',
                    legend=dict(bordercolor='LightGray', borderwidth=1)
                )

                # 6) Render
                st.plotly_chart(fig, use_container_width=True)

        # — in your main app file, under the Statistical Insights tab: —
        capm_vs_regression_widget()




elif tab == "Corporate Metrics Hub":
    st.header("Corporate Metrics Hub")
    st.markdown(
        """
        Welcome to the Corporate Metrics Hub. Here you can compare key financial indicators
        across up to five companies:

        - **Return on Equity (ROE)**: Measures how efficiently a company uses shareholders’ equity to generate profits.  
        - **Debt-to-Equity (D/E)**: Indicates the relative proportion of debt and equity a company uses to finance its assets.  
        - **Free Cash Flow to Firm (FCFF)**: The cash flow available to all investors (debt + equity), after operating expenses and investments.  
        - **Company Info**: Quick access to ticker, sector, and market-cap details.

        Use the controls below to select your companies and metric of interest.
        """
    )

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
    dummy_historical_roes = {ticker: {year: np.random.randint(10, 45) for year in range(2015, 2027)} for ticker in largest_30}
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

        st.subheader(f"Historical {metric_type} (Bar Plot)")
        start_year, end_year = st.slider(
            f"Select Year Range for Historical {metric_type}:",
            min_value=2015,
            max_value=2025,
            value=(2015, 2026),
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
    st.subheader("Discounted Cash Flow Analysis")

    import streamlit as st
    import pandas as pd
    import numpy as np
    import hashlib
    import plotly.graph_objects as go

    # --- DCF Settings ---
    dcf_ticker = st.selectbox(
        "Select company for DCF analysis:",
        options=largest_30,  # your list of tickers
        key="dcf_ticker"
    )

    # --- Build deterministic FCF projection via ticker‐seeded RNG ---
    # create a 32‐bit seed from the ticker string
    seed = int(hashlib.sha256(dcf_ticker.encode()).hexdigest(), 16) & 0xFFFFFFFF
    rng  = np.random.default_rng(seed)

    years = [2023, 2024, 2025, 2026, 2027]
    # generate five random FCFs between $5bn and $15bn
    fcf   = list(np.round(rng.uniform(5, 15, size=len(years)), 2))

    # assumptions
    r = 0.10   # discount rate
    g = 0.02   # terminal growth

    # discount factors & PV of each FCF
    disc_factors = [1 / (1 + r) ** (i + 1) for i in range(len(years))]
    pv_fcf       = [round(f * d, 2) for f, d in zip(fcf, disc_factors)]

    # terminal value and its PV
    terminal_value = fcf[-1] * (1 + g) / (r - g)
    pv_terminal    = round(terminal_value * disc_factors[-1], 2)

    # --- Build DataFrame ---
    df_dcf = pd.DataFrame({
        "Year":             [str(y) for y in years] + ["Terminal"],
        "FCF ($ bn)":       fcf + [None],
        "Discount Factor":  [round(d, 3) for d in disc_factors] + [None],
        "PV of FCF ($ bn)": pv_fcf + [pv_terminal]
    }).set_index("Year")

    st.markdown("## Discounted Cash Flow Analysis")
    st.table(df_dcf)

    # --- NPV Waterfall ---
    labels  = [f"FCF {y}" for y in years] + ["Terminal Value"]
    values  = pv_fcf + [pv_terminal]
    measure = ["relative"] * len(years) + ["total"]

    fig = go.Figure(
        go.Waterfall(
            x=labels,
            y=values,
            measure=measure,
            increasing={"marker": {"color": "green"}},
            totals={"marker": {"color": "blue"}}
        )
    )

    fig.update_layout(
        title=f"NPV Waterfall for {dcf_ticker}",
        yaxis_title="PV (USD bn)",
        template="plotly_dark",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    # … your existing DCF table and waterfall code …

    #st.plotly_chart(fig, use_container_width=True)

    # — now add explanatory text —
    st.markdown(
        """
        **How to read this analysis:**  
        1. The table above lists our **five-year free cash flow (FCF)** projections, the **discount factors** used to bring each year’s cash flow to present value,  
        and the resulting **present value (PV) of each FCF**. The final “Terminal” row shows the perpetuity value of year 5’s cash flow, also discounted back.  
        2. The waterfall chart below visualizes how each year’s PV (green bars) cumulatively builds to the total net present value (blue bar).  
        3. Together, these two views let you see both the line-item detail (yearly cash flows) and the overall NPV impact of the investment under our buy-and-hold assumptions.  

        **Key assumptions:**  
        - **Discount rate (r):** 10% per annum  
        - **Terminal growth (g):** 2% beyond year 5  
        - **Deterministic projections:** We seed our random FCF draws by ticker so that each symbol always yields the same five-year numbers.  
        """
    )

    # --- Inputs ---
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.header("Growth of $1,000 Under Simple vs Compound Interest")
    st.markdown(
        """
        Compare how a lump-sum deposit grows over time under two different approaches:
        1. **Simple Interest**: Interest is paid only on the original principal each period.  
        2. **Compound Interest**: Interest is reinvested, so you earn “interest on interest.”

        **Key takeaways**:  
        - The faster your compounding frequency (e.g., monthly vs. annually), the higher your final balance.  
        - Over longer horizons, compound interest can dramatically outperform simple interest.  
        - Use the controls below to tweak principal, rate, horizon, and compounding options.
        """
    )

    # ─── Inputs ────────────────────────────────────────────────────────
    P = st.number_input("Principal ($)", min_value=0.0, value=1000.0, step=100.0)
    r = st.number_input("Annual rate (%)", min_value=0.0, value=5.0, step=0.1) / 100
    years = st.slider("Time horizon (years)", 1, 30, 10)

    # allow multiple choices
    freqs = st.multiselect(
        "Compounding frequency",
        ["Annually", "Semi-Annually", "Quarterly", "Monthly"],
        default=["Annually", "Semi-Annually", "Quarterly", "Monthly"]
    )

    # map text → n per year
    n_map = {
        "Annually": 1,
        "Semi-Annually": 2,
        "Quarterly": 4,
        "Monthly": 12
    }

    # ─── Build data table ─────────────────────────────────────────────
    t = np.arange(0, years + 1)
    data = {
        "Year": t,
        "Simple Interest": P * (1 + r * t),
    }

    for freq in freqs:
        n = n_map[freq]
        data[f"{freq} Compound"] = P * (1 + r / n) ** (n * t)

    df = pd.DataFrame(data)

    # ─── Plot ────────────────────────────────────────────────────────
    fig = px.line(
        df,
        x="Year",
        y=[c for c in df.columns if c != "Year"],
        labels={"value": "Balance ($)", "variable": "Method"},
        template="plotly_dark",
        title="Growth of $1,000 Under Simple vs. Compound Interest"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Tab 4: Strategy Development ---

elif tab == "Strategy Development":
    st.header("Strategy Development Dashboard")

    # Toggle to Select Strategy View
    strategy_view = st.radio(
        "Select Strategy View:",
        ("Trading Strategies", "Comparative Portfolio Benchmarking", "Efficient Frontier Analysis"),
        horizontal=True
    )

    if strategy_view == "Trading Strategies":
        st.subheader("TS Momentum Strategy")
        st.markdown("""
            A rigorous comparison of a time-series momentum strategy against a passive buy-and-hold approach.  
            The analysis plots cumulative returns generated by a signal that enters and exits positions based 
            on past performance over a defined lookback period. It emphasizes how trend persistence can drive excess growth and how systematic exits may reduce 
            drawdowns during adverse market conditions. Risk and volatility characteristics are presented alongside overall performance to frame the strategy’s 
            reward-to-risk profile in relation to a simple buy-and-hold benchmark.
        """)


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
        st.markdown(
            """
            ### Future Development  
            - **Multi-Asset Expansion:** Extend the strategy beyond equities (e.g. futures, FX, crypto) to demonstrate its robustness across different markets.  
            - **Performance Analytics Dashboard:** Introduce deeper risk metrics (e.g. drawdown heatmaps, rolling Sharpe ratios, Calmar ratio) and interactive charts to explore sub-period performance.  
             """
        )
        # ── At the top of MarketVisionStudio.py ────────────────────────────────────────
        import streamlit as st
        import yfinance as yf
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        from sklearn.preprocessing import StandardScaler
        import tensorflow as tf
        import warnings
        from keras.callbacks  import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau


        from keras.models     import Model
        from keras.layers     import (
            Input, LSTM, Dense, Dropout, BatchNormalization,
            RepeatVector, Lambda, Multiply
        )
        from keras.losses     import Huber
        from keras.optimizers import Adam

        warnings.simplefilter("ignore", UserWarning)


        # ── Helper functions (exactly as in your notebook) ────────────────────────────
        def get_base_price(x):
            # x.shape = (batch, timesteps, features)
            last_close = x[:, -1, 3]  # feature index 3 was “Close”
            return tf.expand_dims(last_close, axis=-1)

        def compute_gain(log_ret):
            return tf.exp(log_ret)


        # ── Build & cache the identical seq2seq LSTM model ─────────────────────────────
        @st.cache_resource
        def load_lstm_model(weights_path: str, timestep: int, n_features: int):
            # Encoder
            enc_in  = Input(shape=(timestep, n_features), name="encoder_input")
            enc_l1  = LSTM(128, return_sequences=False)(enc_in)
            enc_bn  = BatchNormalization()(enc_l1)
            enc_do  = Dropout(0.3)(enc_bn)

            # Decoder
            dec_rep = RepeatVector(timestep)(enc_do)
            dec_l1  = LSTM(64, return_sequences=False)(dec_rep)
            dec_bn  = BatchNormalization()(dec_l1)
            dec_do  = Dropout(0.3)(dec_bn)

            # Output head
            log_ret  = Dense(1, activation="linear", name="log_return")(dec_do)
            base_pr  = Lambda(get_base_price, name="base_price")(enc_in)
            gain     = Lambda(compute_gain,  name="exp_return")(log_ret)
            pred_pr  = Multiply(name="predicted_price")([base_pr, gain])

            model = Model(inputs=enc_in, outputs=pred_pr, name="seq2seq_price_model")
            model.compile(
                loss=Huber(delta=1.0),
                optimizer=Adam(learning_rate=1e-4, clipnorm=1.0)
            )

            model.load_weights(weights_path)
            return model


        # ── LSTM Strategy section ─────────────────────────────────────────────────────
        # ── Helpers & Model Builders ───────────────────────────────────────────────────

        def get_base_price(x):
            last_close = x[:, -1, 3]  # feature index 3 == “Close”
            return tf.expand_dims(last_close, axis=-1)

        def compute_gain(log_ret):
            return tf.exp(log_ret)

        @st.cache_resource
        def load_lstm_model(weights_path: str, timestep: int, n_features: int):
            """Builds & compiles the seq2seq LSTM, loads weights for inference."""
            enc_in  = Input((timestep, n_features), name="encoder_input")
            enc_l1  = LSTM(128, return_sequences=False)(enc_in)
            enc_bn  = BatchNormalization()(enc_l1)
            enc_do  = Dropout(0.3)(enc_bn)

            dec_rep = RepeatVector(timestep)(enc_do)
            dec_l1  = LSTM(64, return_sequences=False)(dec_rep)
            dec_bn  = BatchNormalization()(dec_l1)
            dec_do  = Dropout(0.3)(dec_bn)

            log_ret = Dense(1, activation="linear", name="log_return")(dec_do)
            base_pr = Lambda(get_base_price, name="base_price")(enc_in)
            gain    = Lambda(compute_gain,  name="exp_return")(log_ret)
            pred_pr = Multiply(name="predicted_price")([base_pr, gain])

            m = Model(enc_in, pred_pr, name="seq2seq_price_model")
            m.compile(
                loss=Huber(delta=1.0),
                optimizer=Adam(learning_rate=1e-4, clipnorm=1.0)
            )
            m.load_weights(weights_path)
            return m

        def train_lstm_model(X_np, y_np, timestep: int) -> str:
            """Rebuilds the LSTM, trains it, writes checkpoint.weights.keras, returns filepath."""
            # build identical architecture (no load_weights)
            enc_in  = Input((timestep, X_np.shape[2]), name="encoder_input")
            enc_l1  = LSTM(128, return_sequences=False)(enc_in)
            enc_bn  = BatchNormalization()(enc_l1)
            enc_do  = Dropout(0.3)(enc_bn)
            dec_rep = RepeatVector(timestep)(enc_do)
            dec_l1  = LSTM(64, return_sequences=False)(dec_rep)
            dec_bn  = BatchNormalization()(dec_l1)
            dec_do  = Dropout(0.3)(dec_bn)

            log_ret = Dense(1, activation="linear", name="log_return")(dec_do)
            base_pr = Lambda(get_base_price, name="base_price")(enc_in)
            gain    = Lambda(compute_gain,  name="exp_return")(log_ret)
            pred_pr = Multiply(name="predicted_price")([base_pr, gain])

            m = Model(enc_in, pred_pr, name="seq2seq_price_model")
            m.compile(
                loss=Huber(delta=1.0),
                optimizer=Adam(learning_rate=1e-4, clipnorm=1.0),
                metrics=['mse','mae']
            )

            # callbacks
            fp = "checkpoint.weights.keras"
            cp  = ModelCheckpoint(fp, monitor='val_loss', save_best_only=True, verbose=0)
            es  = EarlyStopping(monitor='val_loss', patience=12, restore_best_weights=True, verbose=0)
            rlr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=6, min_lr=1e-6, verbose=0)

            # Streamlit progress UI
            epochs        = 100
            prog_bar      = st.progress(0)
            status_holder = st.empty()
            hist = {"loss": [], "val_loss": []}
            chart = st.line_chart(pd.DataFrame(hist))

            class ProgressCB(tf.keras.callbacks.Callback):
                def on_epoch_end(self, epoch, logs=None):
                    p = (epoch+1)/epochs
                    prog_bar.progress(p)
                    status_holder.text(f"Epoch {epoch+1}/{epochs}  loss: {logs['loss']:.3f}  val_loss: {logs['val_loss']:.3f}")
                    hist["loss"].append(logs["loss"])
                    hist["val_loss"].append(logs["val_loss"])
                    chart.add_rows(pd.DataFrame(hist, index=range(1,len(hist["loss"])+1)))

            with st.spinner("Retraining LSTM… this may take a couple minutes"):
                m.fit(
                    X_np, y_np,
                    validation_split=0.2,
                    epochs=epochs,
                    batch_size=32,
                    callbacks=[cp, es, rlr, ProgressCB()],
                    verbose=0
                )
            st.success("Retraining complete—best weights saved.")
            return fp


        # ── LSTM Strategy section ─────────────────────────────────────────────────────
        st.subheader("LSTM-Based Prediction Strategy")
        st.markdown("""
            Click **Retrain LSTM Model** to re-fit on IBKR.csv, otherwise
            we’ll load the existing checkpoint weights for inference.
        """)

        # Retrain toggle
        retrain_btn = st.sidebar.button("Retrain LSTM Model")

        # 1) Load & preprocess IBKR.csv
        df = pd.read_csv("IBKR.csv", index_col=0, parse_dates=True).dropna()
        df.index = pd.to_datetime(df.index)
        X = df[['Open','High','Low','Close','Volume']]
        y = df['Last'].shift(-1).dropna()
        y.index = pd.to_datetime(y.index)

        cutoff   = X.index.max() - pd.DateOffset(days=150)
        X_train  = X.loc[X.index < cutoff]
        X_test   = X.loc[X.index >= cutoff]
        y_train  = y.loc[y.index < cutoff]
        y_test   = y.loc[y.index >= cutoff]

        # scale
        scaler    = StandardScaler().fit(X_train)
        X_train[:] = scaler.transform(X_train)
        X_test[:]  = scaler.transform(X_test)

        # sliding windows
        timestep = 20
        # build sliding windows safely
        def make_seq(X_df, y_ser, step):
            seqs, labs = [], []
            max_i = min(len(X_df), len(y_ser))
            for i in range(step, max_i):
                seqs.append(X_df.iloc[i-step:i].values)
                labs.append(y_ser.iloc[i])
            idx = X_df.index[step:max_i]
            return np.array(seqs), np.array(labs), idx

        # build sliding windows
        X_train_np, y_train_np, _       = make_seq(X_train, y_train, timestep)
        X_test_np,  y_test_np,  test_idx = make_seq(X_test,  y_test,  timestep)

        # force numeric dtype (float32)
        X_train_np = X_train_np.astype(np.float32)
        y_train_np = y_train_np.astype(np.float32)
        X_test_np  = X_test_np.astype(np.float32)
        y_test_np  = y_test_np.astype(np.float32)

        # 2) Retrain if requested
        if retrain_btn:
            load_lstm_model.clear()                      # clear cached inference graph
            weights_fp = train_lstm_model(X_train_np, y_train_np, timestep)
        else:
            weights_fp = "checkpoint.weights.keras"
            st.info("Using existing weights—click Retrain to re-fit.")

        # 3) Inference
        model = load_lstm_model(weights_fp, timestep, n_features=5)
        preds = model.predict(X_test_np, verbose=0).flatten()
        perf  = pd.DataFrame({"Predicted": preds, "Actual": y_test_np}, index=test_idx)

        # 4) Plot Spread + BBands
        Spread = perf.Actual - perf.Predicted
        m      = Spread.expanding().mean()
        s      = Spread.expanding().std()
        k      = 2

        fig1, ax1 = plt.subplots(figsize=(10,4))
        ax1.plot(Spread, label="Spread")
        ax1.plot(m + k*s, "--", label="Upper")
        ax1.plot(m - k*s, "--", label="Lower")
        ax1.set_title("Spread vs Predicted (±2σ)")
        ax1.legend(loc="upper left")
        st.pyplot(fig1); plt.close(fig1)

        # 5) Predicted vs Actual + signals
        fig2, ax2 = plt.subplots(figsize=(10,4))
        ax2.plot(perf.Predicted, label="Predicted")
        ax2.plot(perf.Actual,    label="Actual")
        buy_mask  = Spread < (m - k*s)
        sell_mask = Spread > (m + k*s)
        ax2.scatter(perf.index[buy_mask],  perf.Actual[buy_mask],  marker="^", c="green", s=50, label="Buy")
        ax2.scatter(perf.index[sell_mask], perf.Actual[sell_mask], marker="v", c="red",   s=50, label="Sell")
        ax2.set_title("Predicted vs Actual with Buy/Sell Signals")
        ax2.legend(loc="upper left")
        st.pyplot(fig2); plt.close(fig2)

                # … your plotting code …

        st.markdown("""
        ### LSTM-Based Prediction Strategy — Component Breakdown

        **1. Data Ingestion & Pre-processing**  
        - We load `IBKR.csv`, parse dates, and shift the `Last` price by one day to form our label `y`.  
        - We split the series at the 150-day cutoff into **train** and **test** sets.  
        - Features (`Open, High, Low, Close, Volume`) are scaled via `StandardScaler` to zero mean & unit variance.

        **2. Sliding Window Construction**  
        - A fixed look-back of **20** timesteps is used.  
        - For each index *i*, the LSTM sees the matrix of the previous 20 days’ features (shape `(20, 5)`).  
        - Corresponding label is the next-day `Last` price at *i*.

        **3. Model Architecture**  
        - **Seq2Seq LSTM Encoder**: 128 units → BatchNorm → Dropout(0.3)  
        - **Seq2Seq LSTM Decoder**: RepeatVector(20) → 64 units → BatchNorm → Dropout(0.3)  
        - **Output Head**:
          - Dense→linear predicts the **log-return**.  
          - We extract the **base price** (last close) via a `Lambda` layer, exponentiate our log-return, and multiply back to get the absolute next-day price.

        **4. Retraining vs. Inference**  
        - Click **Retrain LSTM Model** in the sidebar to re-fit the network on the training split (with live progress).  
        - Otherwise, the app loads the existing `checkpoint.weights.keras` for instant inference.

        **5. Spread & Bollinger Band Analysis**  
        - We compute **Spread** = Actual − Predicted.  
        - We plot the expanding mean ±2×standard-deviation to highlight over-bought (sell) and over-sold (buy) regions.

        **6. Signal Generation & Visualizations**  
        - **Chart 1** shows the Spread with its Bollinger bands.  
        - **Chart 2** overlays Predicted vs Actual price, marking:
          - ▶️ **Buy** when Spread < Lower Band  
          - 🔻 **Sell** when Spread > Upper Band  

        This systematic framework demonstrates how a pre-trained LSTM can forecast short-term price movements, quantify prediction error via Spread, and generate rule-based entry/exit signals.
        """)

        
    elif strategy_view == "Comparative Portfolio Benchmarking":
        st.markdown("""
        Comparative Portfolio Benchmarking provides a concurrent assessment of multiple passive equity portfolios
         and their corresponding market indices. Under a uniform buy and hold framework, it juxtaposes each portfolio’s 
        cumulative growth with that of its benchmark and presents measures of realized volatility and maximum drawdown. 
        This systematic comparison enables rigorous evaluation of allocation performance and facilitates informed decision 
        making based on both risk and return metrics.
        """)

        st.subheader("Magnificent Seven vs SPY")

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
            ax.set_title("Magnificent Seven Portfolio vs SPY", fontsize=16)
            ax.set_xlabel("Date")
            ax.set_ylabel("Growth of $1 Investment")
            ax.legend()
            st.pyplot(fig)
            plt.close(fig) 
        else:
            st.warning("Please select at least 2 stocks for the portfolio.")

        # 1) Sidebar inputs (you can reuse your existing date widgets)
        #st.sidebar.subheader("Quality Factor Portfolio")
        #q_start = st.sidebar.date_input("Start Date (Quality)", pd.to_datetime("2022-01-01"))
        #q_end   = st.sidebar.date_input("End Date (Quality)",   pd.to_datetime("today"))

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
        st.subheader("Quality Factor Portfolio vs QUAL ETF")

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

        # 1) Date inputs (in the sidebar, with unique keys)
        portfolio_start_d = st.date_input("Portfolio Start Date", pd.to_datetime("2022-01-01"), key = "qd_start_1")
        portfolio_end_d   = st.date_input("Portfolio End Date",   pd.to_datetime("today"), key = "qd_end_1")
        #st.sidebar.subheader("Quality Dividend Portfolio")
        
        qd_start = portfolio_start_d
        qd_end   = portfolio_end_d

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
        st.subheader("Quality Dividend Factor Portfolio vs SDY ETF")

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


        st.header("Efficient Frontier")
        st.markdown("""
            **Efficient Frontier Explained (Best viewed in Full Screen Mode)**  
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
