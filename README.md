# MarketVisionStudio

**MarketVisionStudio** is an end-to-end toolkit for interactive financial market analysis, strategy prototyping, and custom dashboard creation. It combines data ingestion modules, Jupyter notebooks, and lightweight web apps to offer a seamless workflow from live data exploration to backtesting and reporting.

---

## Key Features

* **Data Connectors:** Modular API wrappers for real-time and historical data from Interactive Brokers, Alpha Vantage, Quandl, and yfinance.
* **Interactive Notebooks:** Pre-built Jupyter notebooks for live market dashboards, strategy backtests (momentum, mean-reversion, volatility), and risk analyses.
* **Web Dashboards:** Streamlit and Voilà applications for dynamic visualization and parameter tuning without code modifications.
* **Visualization Toolkit:** Reusable Python modules for candlestick, OHLC, heatmaps, correlation matrices, and risk-return plots.
* **Automated Reporting:** Scripts to generate PDF/HTML performance reports including P\&L charts, drawdowns, and risk factor summaries.

---

## Repository Structure

```plaintext
MarketVisionStudio/
├── data_connectors/          # API wrappers and ingestion scripts
│   ├── ibkr_connector.py     # Interactive Brokers market data client (coming soon)
│   ├── alpha_vantage.py      # Alpha Vantage REST API integration (coming soon)
│   ├── quandl_connector.py   # Quandl data downloader (coming soon)
│   └── yfinance.py           # Yahoo Finance data loader (coming soon)
│
├── notebooks/                # Jupyter notebooks for exploration and backtests
│   ├── Live_Market_Dashboard.ipynb       # Real-time streaming dashboard
│   ├── Momentum_Strategy_Backtest.ipynb  # Backtest template for momentum
│   ├── Mean_Reversion_Template.ipynb     # Mean-reversion backtesting notebook
│   ├── Volatility_Scalping.ipynb         # Volatility scalping prototype
│   └── Risk_Analytics.ipynb              # P&L, drawdown, and risk factor analysis
│
├── dashboards/               # Streamlit and Voilà applications
│   ├── streamlit_app.py      # Main Streamlit dashboard
│   
│
├── reports/                  # Sample generated performance and risk reports
│   └── sample_report.pdf     # Example output
│
├── viz_toolkit/              # Visualization utility modules
│   ├── charts.py             # Common chart functions (candlestick, OHLC)
│   ├── heatmap.py            # Heatmap and correlation matrix helpers
│   └── utils.py              # Utility functions (data formatting, color palettes)
│
├── examples/                 # Example scripts and notebooks (optional)
│   └── quick_start.py        # CLI script demonstrating core features
│
├── requirements.txt          # Python dependencies
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/mano001-ctrl/marketvisionstudio.git
   cd marketvisionstudio
   ```

2. **(Optional) Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # macOS/Linux
   .\.venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Running Notebooks

* Launch Jupyter Lab or Notebook in the project root:

  ```bash
  jupyter lab
  ```
* Open any notebook in `notebooks/` and run cells interactively to explore data and strategy results.

### 2. Launching Streamlit Dashboard

* Run the Streamlit app:

  ```bash
  streamlit run dashboards/streamlit_app.py
  ```
* The app provides live data views, parameter sliders, and downloadable charts.

### 3. Deploying Voilà Dashboard

* Start the Voilà server:

  ```bash
  voila dashboards/voila_template.ipynb
  ```
* Access the dynamically rendered notebook as a standalone web dashboard.

### 4. Generating Reports

* Execute the reporting script to produce performance reports:

  ```bash
  python viz_toolkit/utils.py --generate-report --config reports/config.yaml
  ```
* Sample output available in `reports/sample_report.pdf`.

---

## Contributing

We welcome contributions from the community!

1. **Fork** the repository.
2. Create a new branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests/docs.
4. Commit and push: `git push origin feature/my-feature`
5. Open a Pull Request and describe your enhancements.

Please follow the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/) and ensure notebooks are well-documented.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

For questions, issues, or collaboration opportunities, please open an issue on GitHub or contact the maintainer directly.
