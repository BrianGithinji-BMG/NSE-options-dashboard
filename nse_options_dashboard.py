import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from scipy.stats import norm
import datetime

# --- Page Config ---
st.set_page_config(page_title="NSE Options & Risk Engine", layout="wide", initial_sidebar_state="expanded")

# --- Custom Theme & Styling ---
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
    }
    
    /* Header styling */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    h2, h3 {
        color: #34495e;
        border-bottom: 2px solid #95a5a6;
        padding-bottom: 10px;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #bdc3c7;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #ecf0f1 0%, #d5dbdb 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ecf0f1 0%, #d5dbdb 100%);
        border-right: 1px solid #95a5a6;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 2px solid #95a5a6;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #7f8c8d;
        border-bottom: 3px solid transparent;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2c3e50;
        border-bottom: 3px solid #2c3e50;
    }
    
    /* Slider styling */
    .stSlider [data-baseweb="slider"] {
        background: #ecf0f1 !important;
    }
    
    [data-testid="stSlider"] [role="slider"] {
        background-color: #34495e !important;
    }
    
    /* Input field styling */
    input {
        background-color: #ffffff !important;
        border: 1px solid #bdc3c7 !important;
        color: #2c3e50 !important;
    }
    
    /* Text color - MAIN */
    p {
        color: #2c3e50 !important;
        font-size: 16px;
    }
    
    span {
        color: #2c3e50 !important;
    }
    
    body {
        color: #2c3e50 !important;
    }
    
    /* Table styling */
    [data-testid="stTable"] {
        background-color: #ffffff;
        border: 1px solid #bdc3c7;
        color: #2c3e50;
    }
    
    /* Dataframe styling */
    .streamlit-expanderHeader {
        background-color: #ecf0f1;
        color: #2c3e50;
    }
    
    /* Spinner text */
    .stSpinner {
        color: #34495e;
    }
    
    /* Markdown links */
    a {
        color: #3498db;
    }
    
    /* Caption styling */
    .caption {
        color: #7f8c8d !important;
    }
    
    /* Label text */
    label {
        color: #2c3e50 !important;
    }
    
    .stMarkdown {
        color: #2c3e50 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- MODULE 1: Market Data Engine ---
class MarketDataEngine:
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_data(ticker="SCOM.NR", period="1y"):
        try:
            df = yf.download(ticker, period=period, progress=False)
            if df.empty:
                raise ValueError("No data returned from Yahoo Finance.")
            
            # Extract closing prices
            prices = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
            if isinstance(prices, pd.DataFrame):
                prices = prices.iloc[:, 0]
                
            returns = np.log(prices / prices.shift(1)).dropna()
            volatility = returns.std() * np.sqrt(252)
            drift = returns.mean() * 252 + 0.5 * (volatility ** 2)
            
            return prices, returns, volatility, drift
        except Exception as e:
            # Robust Fallback for NSE API downtime
            st.warning(f"Live fetch for {ticker} unavailable. Loading simulated NSE data profile.")
            dates = pd.date_range(end=datetime.date.today(), periods=252)
            # Simulating Safaricom's typical drift and volatility
            prices = pd.Series(np.cumprod(1 + np.random.normal(0.0002, 0.015, 252)) * 31.0, index=dates)
            returns = np.log(prices / prices.shift(1)).dropna()
            volatility = returns.std() * np.sqrt(252)
            drift = returns.mean() * 252 + 0.5 * (volatility ** 2)
            return prices, returns, volatility, drift

# --- MODULE 2: Black-Scholes Engine ---
class BlackScholesEngine:
    def __init__(self, S, K, T, r, sigma):
        self.S = S
        self.K = K
        self.T = max(T, 1e-5) # Prevent division by zero
        self.r = r
        self.sigma = max(sigma, 1e-5)
        
        self.d1 = (np.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        self.d2 = self.d1 - self.sigma * np.sqrt(self.T)

    def call_price(self):
        return self.S * norm.cdf(self.d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(self.d2)

    def put_price(self):
        return self.K * np.exp(-self.r * self.T) * norm.cdf(-self.d2) - self.S * norm.cdf(-self.d1)

    def greeks(self):
        call_delta = norm.cdf(self.d1)
        put_delta = call_delta - 1
        gamma = norm.pdf(self.d1) / (self.S * self.sigma * np.sqrt(self.T))
        vega = self.S * norm.pdf(self.d1) * np.sqrt(self.T) * 0.01 
        
        call_theta = (-self.S * norm.pdf(self.d1) * self.sigma / (2 * np.sqrt(self.T)) 
                      - self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(self.d2)) / 365
        put_theta = (-self.S * norm.pdf(self.d1) * self.sigma / (2 * np.sqrt(self.T)) 
                     + self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(-self.d2)) / 365
                     
        call_rho = self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(self.d2) * 0.01
        put_rho = -self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(-self.d2) * 0.01

        return {
            "Delta": {"Call": call_delta, "Put": put_delta},
            "Gamma": {"Call": gamma, "Put": gamma},
            "Vega": {"Call": vega, "Put": vega},
            "Theta": {"Call": call_theta, "Put": put_theta},
            "Rho": {"Call": call_rho, "Put": put_rho}
        }

# --- MODULE 3: Monte Carlo Engine ---
class MonteCarloEngine:
    def __init__(self, S, K, T, r, sigma, num_simulations=10000, num_steps=100):
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.N = num_simulations
        self.steps = num_steps

    def simulate_exact_gbm(self, use_antithetic=True):
        np.random.seed(42) # Reproducibility for visual convergence
        dt = self.T / self.steps
        
        # Variance Reduction: Antithetic Variates
        if use_antithetic:
            Z = np.random.standard_normal((int(self.N / 2), self.steps))
            Z = np.concatenate((Z, -Z), axis=0)
        else:
            Z = np.random.standard_normal((self.N, self.steps))
            
        paths = np.zeros((self.N, self.steps + 1))
        paths[:, 0] = self.S
        
        for t in range(1, self.steps + 1):
            paths[:, t] = paths[:, t-1] * np.exp((self.r - 0.5 * self.sigma**2) * dt + self.sigma * np.sqrt(dt) * Z[:, t-1])
            
        return paths

    def price_options(self, paths):
        S_T = paths[:, -1]
        call_payoffs = np.maximum(S_T - self.K, 0)
        put_payoffs = np.maximum(self.K - S_T, 0)
        
        discount_factor = np.exp(-self.r * self.T)
        
        call_price = np.mean(call_payoffs) * discount_factor
        put_price = np.mean(put_payoffs) * discount_factor
        
        # Standard Error & Confidence Intervals
        call_se = np.std(call_payoffs * discount_factor) / np.sqrt(self.N)
        put_se = np.std(put_payoffs * discount_factor) / np.sqrt(self.N)
        
        return {
            "Call": {"Price": call_price, "SE": call_se, "CI_Lower": call_price - 1.96*call_se, "CI_Upper": call_price + 1.96*call_se},
            "Put": {"Price": put_price, "SE": put_se, "CI_Lower": put_price - 1.96*put_se, "CI_Upper": put_price + 1.96*put_se}
        }

# --- MODULE 4: Risk Engine ---
class RiskEngine:
    @staticmethod
    def calculate_var_es(returns, confidence_level=0.95):
        # Historical Method
        hist_var = np.percentile(returns, (1 - confidence_level) * 100)
        hist_es = returns[returns <= hist_var].mean()
        
        # Parametric Method (Normal Distribution Assumption)
        mu = returns.mean()
        sigma = returns.std()
        param_var = norm.ppf(1 - confidence_level, mu, sigma)
        param_es = mu - sigma * (norm.pdf(norm.ppf(1 - confidence_level)) / (1 - confidence_level))
        
        return {
            "Historical VaR": hist_var, "Historical ES": hist_es,
            "Parametric VaR": param_var, "Parametric ES": param_es
        }

# --- MODULE 5: Streamlit Dashboard ---
def main():
    st.title("NSE Option Pricing & Risk Dashboard")
    st.markdown("A quantitative finance engine bridging technical liquidity analysis with institutional pricing models.")
    
    # --- Sidebar Controls ---
    st.sidebar.header("Data Engine")
    ticker = st.sidebar.text_input("Ticker Symbol", value="SCOM.NR")
    
    with st.spinner("Compiling Market Data..."):
        prices, returns, hist_vol, drift = MarketDataEngine.fetch_data(ticker=ticker)
    
    current_price = float(prices.iloc[-1])
    
    st.sidebar.header("Pricing Parameters")
    S = st.sidebar.slider("Spot Price (S)", min_value=1.0, max_value=100.0, value=current_price, step=0.5)
    K = st.sidebar.slider("Strike Price (K)", min_value=1.0, max_value=100.0, value=current_price * 1.05, step=0.5)
    T = st.sidebar.slider("Time to Maturity (Years)", min_value=0.01, max_value=5.0, value=1.0, step=0.01)
    sigma = st.sidebar.slider("Annual Volatility (σ)", min_value=0.01, max_value=1.0, value=float(hist_vol), step=0.01)
    # Defaulting to a higher yield environment typical for Kenyan T-Bills
    r = st.sidebar.slider("Risk-Free Rate (r)", min_value=0.0, max_value=0.25, value=0.15, step=0.005) 
    
    st.sidebar.header("Monte Carlo Parameters")
    N = st.sidebar.slider("Simulations", min_value=1000, max_value=50000, value=10000, step=1000)
    
    # --- Engine Execution ---
    bs_engine = BlackScholesEngine(S, K, T, r, sigma)
    mc_engine = MonteCarloEngine(S, K, T, r, sigma, num_simulations=N)
    
    # --- UI Layout ---
    tab1, tab2, tab3 = st.tabs(["Pricing & Greeks", "Monte Carlo Simulation", "Risk Engine"])
    
    with tab1:
        col1, col2 = st.columns(2)
        bs_call = bs_engine.call_price()
        bs_put = bs_engine.put_price()
        
        col1.metric("Black-Scholes Call", f"KES {bs_call:.4f}")
        col2.metric("Black-Scholes Put", f"KES {bs_put:.4f}")
        
        st.subheader("The Greeks (Sensitivity Matrix)")
        greeks_df = pd.DataFrame(bs_engine.greeks())
        st.dataframe(greeks_df.style.format("{:.4f}"), use_container_width=True)
        
    with tab2:
        st.subheader("Geometric Brownian Motion (GBM) Paths")
        with st.spinner("Simulating Path Evolution..."):
            paths = mc_engine.simulate_exact_gbm(use_antithetic=True)
            mc_results = mc_engine.price_options(paths)
        
        fig = go.Figure()
        # Plotting a subset of paths to keep the browser responsive and visually clean
        for i in range(min(150, N)):
            fig.add_trace(go.Scatter(y=paths[i, :], mode='lines', line=dict(width=1, color='rgba(41, 128, 185, 0.1)'), showlegend=False))
        fig.add_hline(y=K, line_dash="dash", line_color="red", annotation_text="Strike (K)")
        fig.update_layout(title="Simulated Asset Price Paths (Antithetic Variates Enabled)", xaxis_title="Time Steps", yaxis_title="Asset Price (KES)", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Convergence Results")
        col1, col2 = st.columns(2)
        col1.metric("MC Call Price", f"KES {mc_results['Call']['Price']:.4f}", f"Δ to BS: {mc_results['Call']['Price'] - bs_call:.4f}")
        col1.caption(f"**95% CI:** [{mc_results['Call']['CI_Lower']:.4f}, {mc_results['Call']['CI_Upper']:.4f}]")
        
        col2.metric("MC Put Price", f"KES {mc_results['Put']['Price']:.4f}", f"Δ to BS: {mc_results['Put']['Price'] - bs_put:.4f}")
        col2.caption(f"**95% CI:** [{mc_results['Put']['CI_Lower']:.4f}, {mc_results['Put']['CI_Upper']:.4f}]")
        
    with tab3:
        st.subheader("Historical vs Parametric VaR (1-Day Horizon)")
        risk_95 = RiskEngine.calculate_var_es(returns, 0.95)
        risk_99 = RiskEngine.calculate_var_es(returns, 0.99)
        
        risk_df = pd.DataFrame({
            "95% Confidence": [f"{risk_95['Historical VaR']*100:.2f}%", f"{risk_95['Historical ES']*100:.2f}%", f"{risk_95['Parametric VaR']*100:.2f}%", f"{risk_95['Parametric ES']*100:.2f}%"],
            "99% Confidence": [f"{risk_99['Historical VaR']*100:.2f}%", f"{risk_99['Historical ES']*100:.2f}%", f"{risk_99['Parametric VaR']*100:.2f}%", f"{risk_99['Parametric ES']*100:.2f}%"]
        }, index=["Value at Risk (Historical)", "Expected Shortfall (Historical)", "Value at Risk (Parametric)", "Expected Shortfall (Parametric)"])
        
        st.table(risk_df)
        
        st.markdown("---")
        st.subheader("Log Returns Distribution")
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=returns, nbinsx=60, name="Historical Returns", histnorm='probability density', marker_color='slategray'))
        fig2.add_vline(x=risk_95['Historical VaR'], line_dash="dash", line_color="orange", annotation_text="95% VaR")
        fig2.add_vline(x=risk_99['Historical VaR'], line_dash="dash", line_color="red", annotation_text="99% VaR")
        fig2.update_layout(title="Empirical Return Distribution Tail Risk", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
