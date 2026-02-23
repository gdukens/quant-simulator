"""
Macro Analysis Dashboard

Week 12: Streamlit page for macro regime detection and sentiment analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from quantlib_pro.ui import components

# Page config
st.set_page_config(
    page_title="Macro Analysis - QuantLib Pro",
    page_icon="📉",
    layout="wide",
)

st.title("📉 Macro Analysis")
st.markdown("Analyze macroeconomic indicators, market sentiment, and correlation regimes.")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    st.subheader("Analysis Type")
    analysis_type = st.selectbox(
        "Select Analysis",
        ["Macro Regime", "Sentiment Analysis", "Correlation Regime"],
        index=0,
    )
    
    st.subheader("Date Range")
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365*2)
    
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)
    
    analyze_button = st.button("📊 Analyze", type="primary", use_container_width=True)

# Main content
st.info("🚧 **Coming in Week 13**: Full macro analysis dashboard with indicators, sentiment indices, and correlation analysis.")

st.markdown("### Planned Features")

tab1, tab2, tab3 = st.tabs(["📈 Macro Regime", "😱 Sentiment", "🔗 Correlation"])

with tab1:
    st.subheader("Macro Regime Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            #### Economic Indicators
            - GDP growth rate
            - Unemployment rate
            - PMI (Purchasing Managers' Index)
            - CPI & inflation
            - Central bank rates
            """
        )
    
    with col2:
        st.markdown(
            """
            #### Regime Classification
            - **Expansion**: High GDP growth, low unemployment
            - **Slowdown**: Declining indicators
            - **Recession**: Negative growth, rising unemployment
            - **Recovery**: Improving from recession
            """
        )
    
    # Mock visualization
    dates = pd.date_range(start=start_date, end=end_date, freq="M")
    gdp_growth = np.random.normal(2.5, 1.5, len(dates))
    unemployment = np.random.normal(4.5, 0.8, len(dates))
    pmi = np.random.normal(52, 3, len(dates))
    
    macro_df = pd.DataFrame({
        "date": dates,
        "GDP Growth (%)": gdp_growth,
        "Unemployment (%)": unemployment,
        "PMI": pmi,
    })
    
    fig = components.plot_time_series(
        data=macro_df,
        title="Sample: Macro Indicators Over Time",
        x_col="date",
        y_cols=["GDP Growth (%)", "PMI"],
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Market Sentiment Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            #### Sentiment Indicators
            - **VIX**: Fear gauge (volatility index)
            - **Put/Call Ratio**: Options sentiment
            - **Advance/Decline**: Market breadth
            - **Fear & Greed Index**: Composite sentiment
            - **High-Yield Spreads**: Credit risk
            """
        )
    
    with col2:
        st.markdown(
            """
            #### Sentiment Regimes
            - **Extreme Fear**: VIX > 30, high put/call
            - **Neutral**: Balanced indicators
            - **Extreme Greed**: VIX < 15, low put/call
            - **Contrarian Signals**: Extreme readings
            """
        )
    
    # Mock fear & greed gauge
    fear_greed_value = 45  # 0-100
    
    import plotly.graph_objects as go
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fear_greed_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Fear & Greed Index"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "red"},
                {'range': [25, 45], 'color': "orange"},
                {'range': [45, 55], 'color': "yellow"},
                {'range': [55, 75], 'color': "lightgreen"},
                {'range': [75, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(height=300, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"**Current Sentiment**: {'Fear' if fear_greed_value < 45 else 'Greed' if fear_greed_value > 55 else 'Neutral'}")

with tab3:
    st.subheader("Correlation Regime Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            #### Correlation Metrics
            - Average pairwise correlation
            - Correlation stability
            - Eigenvalue concentration
            - Diversification ratio
            - Contagion risk
            """
        )
    
    with col2:
        st.markdown(
            """
            #### Correlation Regimes
            - **Calm** (ρ < 0.3): Low correlation, good diversification
            - **Stress** (0.3 ≤ ρ < 0.6): Rising correlation
            - **Crisis** (ρ ≥ 0.6): High correlation, contagion risk
            """
        )
    
    # Mock correlation matrix
    tickers = ["SPY", "TLT", "GLD", "EEM", "VNQ"]
    np.random.seed(42)
    
    # Generate correlation matrix
    random_matrix = np.random.randn(5, 5)
    corr_matrix = np.corrcoef(random_matrix)
    corr_df = pd.DataFrame(corr_matrix, index=tickers, columns=tickers)
    
    fig = components.plot_correlation_matrix(corr_df, height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    avg_corr = (corr_matrix.sum() - len(tickers)) / (len(tickers) * (len(tickers) - 1))
    
    if avg_corr < 0.3:
        regime = "Calm"
        color = "green"
    elif avg_corr < 0.6:
        regime = "Stress"
        color = "orange"
    else:
        regime = "Crisis"
        color = "red"
    
    st.markdown(f"**Average Correlation**: {avg_corr:.2f}")
    st.markdown(f"**Regime**: :{color}[{regime}]")

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Macro Analysis powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
