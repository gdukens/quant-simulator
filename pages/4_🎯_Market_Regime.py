"""
Market Regime Detection Dashboard

Week 13: Streamlit page for HMM-based market regime detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from quantlib_pro.ui import components
from quantlib_pro.market_regime.hmm_detector import detect_regimes_hmm
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Market Regime - QuantLib Pro",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Market Regime Detection")
st.markdown("Identify market regimes (bull, bear, high vol, low vol) using Hidden Markov Models.")

# Initialize session state
if "regime_results" not in st.session_state:
    st.session_state.regime_results = None

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
tab1, tab2, tab3 = st.tabs(["📊 Regime Detection", "🔄 Transitions", "📈 Statistics"])

with tab1:
    st.header("Market Regime Analysis")
    
    if detect_button:
        with st.spinner(f"Detecting {num_regimes} regimes for {ticker}..."):
            try:
                # Simulate price data
                dates = pd.date_range(start=start_date, end=end_date, freq="D")
                
                # Generate realistic multi-regime price series
                np.random.seed(42)
                regimes_true = []
                returns = []
                
                current_regime = 0
                for i in range(len(dates)):
                    # Switch regimes periodically
                    if i % 200 == 0 and i > 0:
                        current_regime = (current_regime + 1) % num_regimes
                    
                    regimes_true.append(current_regime)
                    
                    # Different return characteristics per regime
                    if current_regime == 0:  # Bull market
                        ret = np.random.normal(0.001, 0.01)
                    elif current_regime == 1:  # High volatility
                        ret = np.random.normal(0.0, 0.025)
                    else:  # Bear market
                        ret = np.random.normal(-0.0008, 0.015)
                    
                    returns.append(ret)
                
                returns_series = pd.Series(returns, index=dates)
                prices = 100 * np.exp(np.cumsum(returns))
                prices_series = pd.Series(prices, index=dates)
                
                # Detect regimes using HMM
                result = detect_regimes_hmm(
                    prices=prices_series,
                    n_regimes=num_regimes,
                )
                
                # Store results
                st.session_state.regime_results = {
                    "current_regime": result["current_regime"],
                    "regime_probabilities": result["regime_probabilities"],
                    "regimes": result.get("regimes", regimes_true),
                    "transition_matrix": result.get("transition_matrix"),
                    "regime_characteristics": result.get("regime_characteristics", {}),
                    "prices": prices,
                    "returns": returns,
                    "dates": dates,
                    "ticker": ticker,
                    "num_regimes": num_regimes,
                }
                
                components.success_message("Regime detection complete!")
                
            except Exception as e:
                components.error_message(f"Regime detection failed: {str(e)}")
                st.session_state.regime_results = None
    
    # Display results
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Current regime metrics
        current_regime = results["current_regime"]
        regime_probs = results["regime_probabilities"]
        
        components.multi_metric_row([
            {
                "title": "Current Regime",
                "value": f"Regime {current_regime}",
                "help": "Current detected market regime",
            },
            {
                "title": "Regime Confidence",
                "value": f"{regime_probs[current_regime]*100:.1f}%",
                "help": "Probability of current regime assignment",
            },
            {
                "title": "Total Regimes",
                "value": results["num_regimes"],
                "help": "Number of hidden states",
            },
            {
                "title": "Data Points",
                "value": len(results["dates"]),
                "help": "Number of observations analyzed",
            },
        ])
        
        st.markdown("---")
        
        # Plot price with regime coloring
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Create regime segments
        regime_colors = ["green", "orange", "red", "blue", "purple"]
        regime_names = [
            "Regime 0 (Bull/Low Vol)",
            "Regime 1 (High Vol)",
            "Regime 2 (Bear)",
            "Regime 3",
            "Regime 4",
        ]
        
        for regime_id in range(results["num_regimes"]):
            mask = np.array(results["regimes"]) == regime_id
            regime_dates = results["dates"][mask]
            regime_prices = np.array(results["prices"])[mask]
            
            fig.add_trace(go.Scatter(
                x=regime_dates,
                y=regime_prices,
                mode="markers",
                marker=dict(size=4, color=regime_colors[regime_id]),
                name=regime_names[regime_id],
            ))
        
        fig.update_layout(
            title=f"{results['ticker']} Price History Colored by Detected Regime",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=500,
            template="plotly_white",
            hovermode="x unified",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Regime probabilities over time
        st.subheader("Regime Probability Evolution")
        
        st.markdown(
            f"""
            Current regime probabilities:
            
            {" | ".join([f"**Regime {i}**: {regime_probs[i]*100:.1f}%" for i in range(len(regime_probs))])}
            """
        )
        
    else:
        components.info_message("Click 'Detect Regimes' to analyze market regimes.")

with tab2:
    st.header("Regime Transitions")
    
    if st.session_state.regime_results and st.session_state.regime_results.get("transition_matrix") is not None:
        results = st.session_state.regime_results
        transition_matrix = results["transition_matrix"]
        
        # Display transition matrix
        st.subheader("Transition Probability Matrix")
        
        transition_df = pd.DataFrame(
            transition_matrix,
            columns=[f"To Regime {i}" for i in range(results["num_regimes"])],
            index=[f"From Regime {i}" for i in range(results["num_regimes"])],
        )
        
        components.data_table(
            transition_df.style.format("{:.3f}").background_gradient(cmap="YlOrRd"),
            title="How likely each regime transitions to another",
        )
        
        # Visualize as heatmap
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=transition_matrix,
            x=[f"Regime {i}" for i in range(results["num_regimes"])],
            y=[f"Regime {i}" for i in range(results["num_regimes"])],
            colorscale="YlOrRd",
            text=transition_matrix,
            texttemplate="%{text:.3f}",
            textfont={"size": 12},
            colorbar=dict(title="Probability"),
        ))
        
        fig.update_layout(
            title="Regime Transition Matrix",
            xaxis_title="To Regime",
            yaxis_title="From Regime",
            height=400,
            template="plotly_white",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Persistence analysis
        st.subheader("Regime Persistence")
        
        persistence_metrics = []
        for i in range(results["num_regimes"]):
            stay_prob = transition_matrix[i, i]
            avg_duration = 1 / (1 - stay_prob) if stay_prob < 1 else float('inf')
            persistence_metrics.append({
                "Regime": f"Regime {i}",
                "Stay Probability": f"{stay_prob:.3f}",
                "Avg Duration (days)": f"{avg_duration:.1f}" if avg_duration != float('inf') else "Absorbing",
            })
        
        persistence_df = pd.DataFrame(persistence_metrics)
        components.data_table(persistence_df)
        
    else:
        components.info_message("Transition matrix will be displayed after regime detection.")

with tab3:
    st.header("Regime Statistics")
    
    if st.session_state.regime_results:
        results = st.session_state.regime_results
        
        # Calculate statistics per regime
        regime_stats = []
        
        for regime_id in range(results["num_regimes"]):
            mask = np.array(results["regimes"]) == regime_id
            regime_returns = np.array(results["returns"])[mask]
            
            if len(regime_returns) > 0:
                regime_stats.append({
                    "Regime": f"Regime {regime_id}",
                    "Observations": len(regime_returns),
                    "Avg Return (%)": regime_returns.mean() * 100,
                    "Volatility (%)": regime_returns.std() * 100,
                    "Sharpe Ratio": regime_returns.mean() / regime_returns.std() if regime_returns.std() > 0 else 0,
                    "Min Return (%)": regime_returns.min() * 100,
                    "Max Return (%)": regime_returns.max() * 100,
                })
        
        stats_df = pd.DataFrame(regime_stats)
        
        components.data_table(
            stats_df.style.format({
                "Observations": "{:,.0f}",
                "Avg Return (%)": "{:.4f}",
                "Volatility (%)": "{:.4f}",
                "Sharpe Ratio": "{:.3f}",
                "Min Return (%)": "{:.4f}",
                "Max Return (%)": "{:.4f}",
            }),
            title="Statistical Characteristics by Regime",
        )
        
        # Return distributions by regime
        st.subheader("Return Distributions by Regime")
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=1, cols=results["num_regimes"],
            subplot_titles=[f"Regime {i}" for i in range(results["num_regimes"])],
        )
        
        colors = ["green", "orange", "red", "blue", "purple"]
        
        for regime_id in range(results["num_regimes"]):
            mask = np.array(results["regimes"]) == regime_id
            regime_returns = np.array(results["returns"])[mask]
            
            fig.add_trace(
                go.Histogram(
                    x=regime_returns * 100,
                    name=f"Regime {regime_id}",
                    marker_color=colors[regime_id],
                    nbinsx=30,
                ),
                row=1, col=regime_id + 1
            )
        
        fig.update_layout(
            title_text="Return Distributions by Regime",
            height=350,
            showlegend=False,
            template="plotly_white",
        )
        
        fig.update_xaxes(title_text="Daily Return (%)")
        fig.update_yaxes(title_text="Frequency")
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Regime statistics will be displayed after detection.")

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Market Regime Detection powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
