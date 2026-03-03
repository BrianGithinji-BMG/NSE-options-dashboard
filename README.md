# NSE Option Pricing & Risk Dashboard
A computational finance project implementing a full pricing and risk engine for NSE equities. Includes Black–Scholes analytical pricing, Monte Carlo simulation with variance reduction, Greeks computation, and multi-method Value-at-Risk (Historical, Parametric, Monte Carlo) using real market data.


---

##  Overview

This dashboard implements:

- Black–Scholes analytical option pricing
- Monte Carlo simulation (exact GBM discretization)
- Variance reduction techniques (Antithetic variates)
- Greeks computation (Delta, Gamma, Vega, Theta, Rho)
- Historical Value-at-Risk (VaR)
- Parametric (Gaussian) VaR
- Monte Carlo VaR
- Expected Shortfall (CVaR)

All parameters are calibrated using real NSE equity data (e.g., Safaricom - `SCOM.NR`).

---

##  Quantitative Framework

### 1️. Asset Dynamics

Under the risk-neutral measure:

dS_t = r S_t dt + σ S_t dW_t

Exact solution:

S_T = S_0 exp((r - ½σ²)T + σ√T Z)

where Z ~ N(0,1)

---

### 2️. Option Pricing

European call option priced using:

- Closed-form Black–Scholes formula
- Monte Carlo estimator:

Ĉ = e^{-rT} (1/N) Σ (S_T^(i) - K)^+

Confidence intervals computed via Central Limit Theorem.

---

### 3. Risk Engine

**Historical VaR**
- Empirical percentile of historical log returns

**Parametric VaR**
- Gaussian assumption:
  
VaR = μ − z_α σ

**Monte Carlo VaR**
- Simulated return distribution using calibrated GBM

**Expected Shortfall**
- Conditional loss beyond VaR threshold

---

##   Tech Stack

- Python
- NumPy
- SciPy
- Pandas
- Matplotlib
- yfinance (market data)
- Streamlit (dashboard layer)

---

##  Features

- Real-time NSE data integration
- Adjustable strike, maturity, volatility
- Monte Carlo simulation count control
- Convergence visualization
- Greeks sensitivity analysis
- Portfolio risk summary panel
- Clean institutional-style UI

---

## 📁 Project Structure
