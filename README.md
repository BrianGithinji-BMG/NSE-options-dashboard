# NSE Option Pricing & Risk Dashboard

A quantitative finance engine for NSE options pricing and risk analysis using Black-Scholes models, Monte Carlo simulations, and VaR/ES risk metrics.

## Features

- **Pricing & Greeks Module**: Real-time Black-Scholes option pricing with Delta, Gamma, Vega, Theta, and Rho calculations
- **Monte Carlo Simulation**: GBM path simulations with antithetic variates variance reduction
- **Risk Engine**: Historical and parametric VaR/ES calculations with interactive risk visualizations
- **Live Market Data**: Yahoo Finance integration with fallback to simulated NSE data

## Installation

### Prerequisites
- Python 3.10+
- Windows/Mac/Linux

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run nse_options_dashboard.py
```

3. Open your browser to `http://localhost:8501`

## Usage

### Sidebar Controls
- **Data Engine**: Enter ticker symbol (e.g., SCOM.NR for Safaricom)
- **Pricing Parameters**: Adjust spot price, strike, time to maturity, volatility, and risk-free rate
- **Monte Carlo Parameters**: Configure number of simulations (1K-50K)

### Dashboard Tabs

1. **Pricing & Greeks**: View option prices and sensitivity metrics
2. **Monte Carlo Simulation**: Visualize asset price paths and convergence analysis
3. **Risk Engine**: Analyze tail risk with VaR/ES metrics and return distributions

## Configuration

Default parameters:
- Ticker: SCOM.NR (Safaricom)
- Time Horizon: 1 year
- Risk-Free Rate: 15% (Kenyan T-Bill yield)
- Simulations: 10,000

## Files

- `nse_options_dashboard.py` - Main application file
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Theme

Professional grey and white theme with:
- Clean light grey background
- Dark grey text for readability
- White metric cards with subtle shadows
- Professional borders and spacing

## Deployment

The application is live on Streamlit:

[https://briangithinji-bmg-nse-options-dash-nse-options-dashboard-m051ki.streamlit.app/](https://briangithinji-bmg-nse-options-dash-nse-options-dashboard-m051ki.streamlit.app/)

## Support

For issues or feature requests, check the application logs in the terminal.

---
**Version**: 1.0  
**Last Updated**: March 3, 2026
