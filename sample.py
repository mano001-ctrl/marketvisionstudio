# Time Series Momentum Strategy - Flexible Package (Updated Local CSV Loader)

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from hurst import compute_Hc  # Hurst exponent computation

# --- Investment Settings ---
initial_capital = 10000
max_alloc_per_class = 2500

# --- Load and Prepare Data ---
def load_prices(csv_path='adj_close_prices.csv'):
    """Load security prices from a local CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Local CSV file {csv_path} not found!")
    prices = pd.read_csv(csv_path, index_col=0, encoding='latin1')
    prices.index = pd.to_datetime(prices.index, dayfirst=True, format='mixed')
    prices = prices.asfreq('BM')
    return prices

# --- Core Strategy Functions ---
def get_ts_mom_strategy_returns(data, lookback=12, hold=3):
    df = pd.DataFrame()
    df['lookback_returns'] = data.pct_change(lookback)
    df['future_returns'] = data.pct_change(hold).shift(-hold)
    df = df.dropna()
    df['positions'] = np.where(df['lookback_returns'] > 0, 1, -1)
    df['strategy_returns'] = df['future_returns'] * df['positions']
    return df['strategy_returns']

def get_hurst_strategy_returns(data, lookback=12, hold=3, hurst_threshold=0.5):
    df = pd.DataFrame()
    df['lookback_returns'] = data.pct_change(lookback)
    df['future_returns'] = data.pct_change(hold).shift(-hold)
    df = df.dropna()
    hurst_value = compute_Hc(data.dropna(), kind='price')[0]
    df['positions'] = np.where(hurst_value > hurst_threshold, 1, -1)
    df['strategy_returns'] = df['future_returns'] * df['positions']
    return df['strategy_returns']

def get_volatility_breakout_strategy(prices, vol_end='2018-12-31', start_date='2000-01-01'):
    data_pc = prices.pct_change()
    data_std = data_pc.loc[:vol_end].std() * np.sqrt(252) * 100
    tickers = data_std.sort_values(ascending=False).iloc[:int(len(data_std) * 0.1)].index
    stock_data = prices.loc[start_date:, tickers]
    stock_data_pc = stock_data.pct_change()
    port = pd.DataFrame()
    port['returns'] = stock_data_pc.mean(axis=1).dropna()
    port['value'] = (port['returns'] + 1).cumprod()
    port['high'] = port['value'].rolling(window=3).max()
    port['signal'] = np.where(port['value'] >= port['high'], 1, 0)
    port['str_returns'] = port['returns'].shift(-1) * port['signal']
    return port

# --- Performance Analytics ---
def plot_returns_dd(portfolio):
    # Sharpe Ratio
    sharpe_ratio = portfolio['str_returns'].mean() / portfolio['str_returns'].std() * np.sqrt(252)
    print(f"The Sharpe ratio is {sharpe_ratio:.2f}")

    # Cumulative Returns
    portfolio['cum_str_returns'] = (portfolio['str_returns'] + 1).cumprod()
    final = portfolio['cum_str_returns'].iloc[-1]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.plot(portfolio.index, portfolio['cum_str_returns'], lw=2, label='Cumulative Returns')
    # Annotate final point
    ax.annotate(
        f"{(final-1)*100:.2f}%",
        xy=(portfolio.index[-1], final),
        xytext=(-50, 10),
        textcoords='offset points',
        fontsize=12,
        arrowprops=dict(arrowstyle='->')
    )
    ax.set_title(f"Strategy Returns (Cumulative: {(final-1)*100:.2f}%)", fontsize=14)
    ax.set_ylabel('Cumulative Returns')
    ax.legend(loc='upper left')
    ax.grid(True)
    plt.show()

    # Drawdown
    running_max = np.maximum.accumulate(portfolio['cum_str_returns'])
    running_max[running_max < 1] = 1
    drawdown = portfolio['cum_str_returns'] / running_max - 1
    max_dd = drawdown.min() * 100
    print(f"The maximum drawdown is {max_dd:.2f}%")

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.plot(portfolio.index, drawdown, lw=2, label='Drawdown', color='red')
    ax2.fill_between(portfolio.index, drawdown, alpha=0.3, color='red')
    ax2.set_title('Drawdown', fontsize=14)
    ax2.set_ylabel('Drawdown')
    ax2.legend(loc='upper left')
    ax2.grid(True)
    plt.show()

# --- Utility Functions ---
def calculate_drawdown(cum_returns):
    return cum_returns / np.maximum.accumulate(cum_returns) - 1

def rolling_sharpe(returns, window=12):
    return returns.rolling(window).mean() / returns.rolling(window).std() * np.sqrt(12)

# --- Strategy Grid Search ---
def grid_search_top3(prices, assets, lookback_range, hold_range, strategy='classic'):
    results = []
    if strategy == 'volatility_breakout':
        port = get_volatility_breakout_strategy(prices)
        rets = port['str_returns'] * 100
        sharpe = port['str_returns'].mean() / port['str_returns'].std() * np.sqrt(252)
        results.append((sharpe, None, None, rets.to_frame(name='VolatilityBreakout')))
        return results
    for lb in lookback_range:
        for hd in hold_range:
            if strategy == 'hurst':
                rets = prices[assets].apply(lambda x: get_hurst_strategy_returns(x, lb, hd)) * 100
            else:
                rets = prices[assets].apply(lambda x: get_ts_mom_strategy_returns(x, lb, hd)) * 100
            eq_w = rets.mean(axis=1)
            if eq_w.std() == 0 or eq_w.isna().any():
                continue
            sharpe = eq_w.mean() / eq_w.std() * np.sqrt(12)
            results.append((sharpe, lb, hd, rets))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:3]

# --- Allocation Cap ---
def cap_returns_by_asset_class(rets, asset_classes, initial_capital, max_alloc_per_class):
    capped = pd.DataFrame(index=rets.index)
    for cls, assets_list in asset_classes.items():
        valid = [a for a in assets_list if a in rets.columns]
        if not valid:
            continue
        class_ret = rets[valid].mean(axis=1)
        capped[cls] = class_ret * (max_alloc_per_class / initial_capital)
    return capped.sum(axis=1)

# --- Main Execution ---
if __name__ == '__main__':
    prices = load_prices()
    # Define asset lists as before...
    strategy = 'volatility_breakout'
    if strategy == 'volatility_breakout':
        port = get_volatility_breakout_strategy(prices)
        plot_returns_dd(port)
    else:
        lb_range = range(1, 13)
        h_range = range(1, 6)
        top3 = grid_search_top3(prices, [], lb_range, h_range, strategy)
        for idx, (sh, lb, hd, rets) in enumerate(top3, 1):
            print(f"Top {idx}: Lookback={lb}, Hold={hd}, Sharpe={sh:.2f}")
            port = pd.DataFrame(rets.mean(axis=1)/100, columns=['str_returns'])
            plot_returns_dd(port)
        df1 = cap_returns_by_asset_class(top3[0][3], {}, initial_capital, max_alloc_per_class)
        monthly = (df1/100 + 1).resample('M').prod() - 1
        monthly.to_csv('monthly_returns_and_contributions.csv')
        print("\nSaved monthly returns to 'monthly_returns_and_contributions.csv'.")
