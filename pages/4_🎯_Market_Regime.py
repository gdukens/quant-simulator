"""
Market Regime Detection Dashboard

Week 12: Streamlit page for HMM-based market regime detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from quantlib_pro.ui import components
from quantlib_pro.market_regime.hmm_detector import detect_regimes_hmm

# Page config
st.set_page_config(
    page_title="Market Regime - QuantLib Pro",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Market Regime Detection")
st.markdown("Identify market regimes (bull, bear, high vol, low vol) using Hidden Markov Models.")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    ticker = st.text_input("Ticker", value="SPY", help="Ticker symbol for regime analysis")
    
    st.subheader("Date Range")
    default_end = datetime.now()
    default_start = default_end - timedelta(days=730)  # 2 years
    
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)
    
    num_regimes = st.slider(
        "Number of Regimes",
        min_value=2,
        max_value=5,
        value=3,
        help="Number of hidden states to detect",
    )
    
    detect_button = st.button("🔍 Detect Regimes", type="primary", use_container_width=True)

# Main content
st.info("🚧 **Coming in Week 13**: Full market regime detection dashboard with HMM analysis, regime transitions, and visualization.")

st.markdown("### Planned Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        #### Regime Detection
        - Hidden Markov Model (HMM) with 2-5 states
        - Automatic regime classification (bull/bear/volatile)
        - Real-time regime probability estimates
        - Regime transition matrix visualization
        """
    )
    
with col2:
    st.markdown(
        """
        #### Analysis Tools
        - Regime persistence metrics
        - Return distributions by regime
        - Volatility clustering analysis
        - Regime prediction confidence
        """
    )

st.markdown("### Sample Output")

# Mock data visualization
dates = pd.date_range(start=start_date, end=end_date, freq="D")
np.random.seed(42)

# Simulate price with regime changes
regimes = []
current_regime = 0
for i in range(len(dates)):
    if i % 150 == 0:  # Change regime every ~150 days
        current_regime = (current_regime + 1) % 3
    regimes.append(current_regime)

prices = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.015, len(dates))))

sample_df = pd.DataFrame({
    "date": dates,
    "price": prices,
    "regime": regimes,
})

# Plot sample
import plotly.graph_objects as go

fig = go.Figure()

# Color by regime
for regime_id in range(3):
    regime_data = sample_df[sample_df["regime"] == regime_id]
    regime_names = ["Low Vol Bull", "High Vol", "Bear"]
    colors = ["green", "orange", "red"]
    
    fig.add_trace(go.Scatter(
        x=regime_data["date"],
        y=regime_data["price"],
        mode="markers",
        marker=dict(size=3, color=colors[regime_id]),
        name=regime_names[regime_id],
    ))

fig.update_layout(
    title="Sample: Price History Colored by Detected Regime",
    xaxis_title="Date",
    yaxis_title="Price ($)",
    height=400,
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Market Regime Detection powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
