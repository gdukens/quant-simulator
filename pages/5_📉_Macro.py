"""
Macro Analysis Dashboard

Week 13: Streamlit page for macro regime detection and sentiment analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from quantlib_pro.ui import components
from quantlib_pro.macro.macro_regime import detect_macro_regime
from quantlib_pro.macro.sentiment import fear_greed_index, vix_sentiment_level
from quantlib_pro.macro.correlation_regime import correlation_regime

# Page config
st.set_page_config(
    page_title="Macro Analysis - QuantLib Pro",
    page_icon="📉",
    layout="wide",
)

st.title("📉 Macro Analysis")
st.markdown("Analyze macroeconomic indicators, market sentiment, and correlation regimes.")

# Initialize session state
if "macro_results" not in st.session_state:
    st.session_state.macro_results = None

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

tab1, tab2, tab3 = st.tabs(["📈 Macro Regime", "😱 Sentiment", "🔗 Correlation"])

with tab1:
    st.header("Macro Regime Detection")
    
    if analyze_button and analysis_type == "Macro Regime":
        with st.spinner("Analyzing macroeconomic regime..."):
            try:
                # Simulate macro indicators
                np.random.seed(42)
                gdp_growth = np.random.normal(2.5, 0.8)
                unemployment = np.random.normal(4.2, 0.5)
                pmi = np.random.normal(52.5, 2.0)
                
                # Detect macro regime
                result = detect_macro_regime(
                    gdp_growth=gdp_growth,
                    unemployment=unemployment,
                    pmi=pmi,
                )
                
                st.session_state.macro_results = {
                    "type": "macro_regime",
                    "current_regime": result["current_regime"],
                    "indicators": result["indicators"],
                    "recession_probability": result.get("recession_probability", 0.15),
                    "gdp_growth": gdp_growth,
                    "unemployment": unemployment,
                    "pmi": pmi,
                }
                
                components.success_message("Macro regime analysis complete!")
                
            except Exception as e:
                components.error_message(f"Analysis failed: {str(e)}")
                st.session_state.macro_results = None
    
    if st.session_state.macro_results and st.session_state.macro_results.get("type") == "macro_regime":
        results = st.session_state.macro_results
        
        # Regime indicators
        regime = results["current_regime"]
        recession_prob = results["recession_probability"]
        
        # Color code regime
        if regime == "EXPANSION":
            color = "green"
            emoji = "📈"
        elif regime == "SLOWDOWN":
            color = "orange"
            emoji = "⚠️"
        elif regime == "RECESSION":
            color = "red"
            emoji = "📉"
        else:  # RECOVERY
            color = "blue"
            emoji = "🔄"
        
        st.markdown(f"## {emoji} Current Regime: :{color}[{regime}]")
        
        # Metrics
        components.multi_metric_row([
            {
                "title": "GDP Growth",
                "value": f"{results['gdp_growth']:.2f}%",
                "help": "Annualized GDP growth rate",
            },
            {
                "title": "Unemployment",
                "value": f"{results['unemployment']:.1f}%",
                "help": "Unemployment rate",
            },
            {
                "title": "PMI",
                "value": f"{results['pmi']:.1f}",
                "help": "Purchasing Managers' Index (>50 = expansion)",
            },
            {
                "title": "Recession Probability",
                "value": f"{recession_prob*100:.1f}%",
                "help": "Estimated probability of recession in next 12 months",
            },
        ])
        
        st.markdown("---")
        
        # Historical indicators (simulated)
        dates = pd.date_range(start=start_date, end=end_date, freq="M")
        
        gdp_hist = 2.5 + np.cumsum(np.random.normal(0, 0.3, len(dates)))
        unemp_hist = 4.5 + np.cumsum(np.random.normal(0, 0.1, len(dates)))
        pmi_hist = 52 + np.cumsum(np.random.normal(0, 1, len(dates)))
        
        macro_df = pd.DataFrame({
            "date": dates,
            "GDP Growth (%)": gdp_hist,
            "Unemployment (%)": unemp_hist,
            "PMI": pmi_hist,
        })
        
        # Plot indicators
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=("GDP Growth (%)", "Unemployment (%)", "PMI"),
            vertical_spacing=0.1,
        )
        
        fig.add_trace(
            go.Scatter(x=macro_df["date"], y=macro_df["GDP Growth (%)"],
                      mode="lines", name="GDP Growth", line=dict(color="green")),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=macro_df["date"], y=macro_df["Unemployment (%)"],
                      mode="lines", name="Unemployment", line=dict(color="red")),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=macro_df["date"], y=macro_df["PMI"],
                      mode="lines", name="PMI", line=dict(color="blue")),
            row=3, col=1
        )
        
        # Add reference lines
        fig.add_hline(y=50, line_dash="dash", line_color="gray", row=3, col=1)
        
        fig.update_layout(
            height=600,
            template="plotly_white",
            showlegend=False,
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Regime interpretation
        st.subheader("Regime Interpretation")
        
        if regime == "EXPANSION":
            st.success(
                """
                🟢 **EXPANSION**: Healthy economic growth with low unemployment.
                - GDP growth above trend
                - Unemployment declining or low
                - PMI in expansion territory (>50)
                - **Investment Strategy**: Risk-on, growth stocks, cyclicals
                """
            )
        elif regime == "SLOWDOWN":
            st.warning(
                """
                🟠 **SLOWDOWN**: Economic growth moderating, early warning signs.
                - GDP growth slowing
                - Unemployment starting to rise
                - PMI near 50 or declining
                - **Investment Strategy**: Rotate to defensives, reduce duration risk
                """
            )
        elif regime == "RECESSION":
            st.error(
                """
                🔴 **RECESSION**: Economic contraction, rising unemployment.
                - Negative GDP growth
                - Rising unemployment
                - PMI below 50
                - **Investment Strategy**: Defensives, quality, government bonds
                """
            )
        else:  # RECOVERY
            st.info(
                """
                🔵 **RECOVERY**: Emerging from recession, early-cycle dynamics.
                - GDP growth turning positive
                - Unemployment stabilizing
                - PMI improving
                - **Investment Strategy**: Cyclicals, reflation trades, commodities
                """
            )
    
    else:
        components.info_message("Click 'Analyze' with 'Macro Regime' selected to detect economic regime.")

with tab2:
    st.header("Market Sentiment Analysis")
    
    if analyze_button and analysis_type == "Sentiment Analysis":
        with st.spinner("Analyzing market sentiment..."):
            try:
                # Calculate sentiment metrics
                fear_greed = fear_greed_index()
                
                # Simulate VIX and other sentiment indicators
                vix_level = np.random.uniform(12, 35)
                put_call_ratio = np.random.uniform(0.6, 1.4)
                advance_decline = np.random.uniform(-0.2, 0.3)
                
                vix_sentiment = vix_sentiment_level(vix_level)
                
                # Determine overall sentiment
                if fear_greed < 25:
                    sentiment_label = "Extreme Fear"
                    color = "red"
                elif fear_greed < 45:
                    sentiment_label = "Fear"
                    color = "orange"
                elif fear_greed < 55:
                    sentiment_label = "Neutral"
                    color = "gray"
                elif fear_greed < 75:
                    sentiment_label = "Greed"
                    color = "lightgreen"
                else:
                    sentiment_label = "Extreme Greed"
                    color = "green"
                
                # Contrarian signal
                if fear_greed < 20:
                    contrarian = "Strong BUY"
                elif fear_greed < 40:
                    contrarian = "BUY"
                elif fear_greed < 60:
                    contrarian = "NEUTRAL"
                elif fear_greed < 80:
                    contrarian = "SELL"
                else:
                    contrarian = "Strong SELL"
                
                st.session_state.macro_results = {
                    "type": "sentiment",
                    "fear_greed_index": fear_greed,
                    "sentiment_label": sentiment_label,
                    "color": color,
                    "vix": vix_level,
                    "vix_sentiment": vix_sentiment,
                    "put_call_ratio": put_call_ratio,
                    "advance_decline": advance_decline,
                    "contrarian_signal": contrarian,
                }
                
                components.success_message("Sentiment analysis complete!")
                
            except Exception as e:
                components.error_message(f"Analysis failed: {str(e)}")
                st.session_state.macro_results = None
    
    if st.session_state.macro_results and st.session_state.macro_results.get("type") == "sentiment":
        results = st.session_state.macro_results
        
        # Fear & Greed Gauge
        import plotly.graph_objects as go
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=results["fear_greed_index"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Fear & Greed Index", 'font': {'size': 24}},
            delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "darkblue", 'thickness': 0.3},
                'steps': [
                    {'range': [0, 25], 'color': "darkred"},
                    {'range': [25, 45], 'color': "orange"},
                    {'range': [45, 55], 'color': "yellow"},
                    {'range': [55, 75], 'color': "lightgreen"},
                    {'range': [75, 100], 'color': "darkgreen"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': results["fear_greed_index"]
                }
            }
        ))
        
        fig.update_layout(height=350, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"## Current Sentiment: :{results['color']}[{results['sentiment_label']}]")
        
        # Sentiment metrics
        components.multi_metric_row([
            {
                "title": "Fear & Greed",
                "value": f"{results['fear_greed_index']:.0f}/100",
                "help": "Composite sentiment index (0=extreme fear, 100=extreme greed)",
            },
            {
                "title": "VIX Level",
                "value": f"{results['vix']:.1f}",
                "help": "Volatility Index (fear gauge)",
            },
            {
                "title": "Put/Call Ratio",
                "value": f"{results['put_call_ratio']:.2f}",
                "help": "Ratio of put to call options (>1 = bearish)",
            },
            {
                "title": "Contrarian Signal",
                "value": results["contrarian_signal"],
                "help": "Contrarian trading signal based on sentiment extremes",
            },
        ])
        
        st.markdown("---")
        
        # Component breakdown
        st.subheader("Sentiment Components")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                f"""
                **VIX Sentiment**: {results['vix_sentiment']}
                - VIX < 15: Complacency
                - VIX 15-25: Normal
                - VIX > 25: Fear
                
                **Put/Call Ratio**: {results['put_call_ratio']:.2f}
                - < 0.7: Bullish extreme
                - 0.7-1.0: Neutral
                - > 1.0: Bearish
                """
            )
        
        with col2:
            st.markdown(
                f"""
                **Advance/Decline**: {results['advance_decline']:.2f}
                - Positive: Broad market strength
                - Negative: Narrow leadership
                
                **Contrarian View**:
                {results['contrarian_signal']}
                """
            )
        
        # Historical sentiment (simulated)
        st.subheader("Sentiment Evolution")
        
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        sentiment_hist = 50 + np.cumsum(np.random.normal(0, 5, len(dates)))
        sentiment_hist = np.clip(sentiment_hist, 0, 100)
        
        sentiment_df = pd.DataFrame({
            "date": dates,
            "Fear & Greed": sentiment_hist,
        })
        
        fig = components.plot_time_series(
            data=sentiment_df,
            title="Fear & Greed Index - Historical",
            x_col="date",
            y_cols=["Fear & Greed"],
            height=300,
        )
        
        # Add horizontal reference lines
        fig.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Extreme Fear")
        fig.add_hline(y=75, line_dash="dash", line_color="green", annotation_text="Extreme Greed")
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Click 'Analyze' with 'Sentiment Analysis' selected to analyze market sentiment.")

with tab3:
    st.header("Correlation Regime Analysis")
    
    if analyze_button and analysis_type == "Correlation Regime":
        with st.spinner("Analyzing correlation regime..."):
            try:
                # Simulate correlation data
                tickers = ["SPY", "TLT", "GLD", "EEM", "VNQ", "QQQ", "IWM", "EFA"]
                n_assets = len(tickers)
                
                # Generate realistic correlation matrix
                np.random.seed(42)
                # Start with random eigenvalues
                eigenvalues = np.random.exponential(1, n_assets)
                eigenvalues = eigenvalues / eigenvalues.sum() * n_assets
                
                # Generate random orthogonal matrix
                Q, _ = np.linalg.qr(np.random.randn(n_assets, n_assets))
                
                # Construct correlation matrix
                corr_matrix = Q @ np.diag(eigenvalues) @ Q.T
                
                # Scale to correlation matrix
                D = np.sqrt(np.diag(corr_matrix))
                corr_matrix = corr_matrix / np.outer(D, D)
                np.fill_diagonal(corr_matrix, 1.0)
                
                # Calculate average correlation
                avg_correlation = (corr_matrix.sum() - n_assets) / (n_assets * (n_assets - 1))
                
                # Detect correlation regime
                regime_result = correlation_regime(avg_correlation)
                
                # Calculate metrics
                eigenvalue_concentration = (eigenvalues[0] / eigenvalues.sum())
                diversification_ratio = np.sqrt(n_assets) / np.sqrt(eigenvalues[0])
                
                st.session_state.macro_results = {
                    "type": "correlation",
                    "correlation_matrix": corr_matrix,
                    "tickers": tickers,
                    "avg_correlation": avg_correlation,
                    "regime": regime_result.name if hasattr(regime_result, 'name') else str(regime_result),
                    "eigenvalues": eigenvalues,
                    "eigenvalue_concentration": eigenvalue_concentration,
                    "diversification_ratio": diversification_ratio,
                }
                
                components.success_message("Correlation analysis complete!")
                
            except Exception as e:
                components.error_message(f"Analysis failed: {str(e)}")
                st.session_state.macro_results = None
    
    if st.session_state.macro_results and st.session_state.macro_results.get("type") == "correlation":
        results = st.session_state.macro_results
        
        avg_corr = results["avg_correlation"]
        regime = results["regime"]
        
        # Color code regime
        if avg_corr < 0.3:
            color = "green"
            emoji = "🟢"
            description = "Low correlation - Good diversification"
        elif avg_corr < 0.6:
            color = "orange"
            emoji = "🟠"
            description = "Rising correlation - Stress building"
        else:
            color = "red"
            emoji = "🔴"
            description = "High correlation - Crisis/Contagion risk"
        
        st.markdown(f"## {emoji} Correlation Regime: :{color}[{regime}]")
        st.markdown(f"*{description}*")
        
        # Metrics
        components.multi_metric_row([
            {
                "title": "Avg Correlation",
                "value": f"{avg_corr:.3f}",
                "help": "Average pairwise correlation",
            },
            {
                "title": "Regime",
                "value": regime,
                "help": "Calm (<0.3), Stress (0.3-0.6), Crisis (>0.6)",
            },
            {
                "title": "Eigenvalue Concentration",
                "value": f"{results['eigenvalue_concentration']*100:.1f}%",
                "help": "% of variance explained by first principal component",
            },
            {
                "title": "Diversification Ratio",
                "value": f"{results['diversification_ratio']:.2f}",
                "help": "Effective diversification (higher = better)",
            },
        ])
        
        st.markdown("---")
        
        # Correlation matrix heatmap
        corr_df = pd.DataFrame(
            results["correlation_matrix"],
            index=results["tickers"],
            columns=results["tickers"],
        )
        
        fig = components.plot_correlation_matrix(corr_df, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Eigenvalue analysis
        st.subheader("Principal Component Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Eigenvalue bar chart
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[f"PC{i+1}" for i in range(len(results["eigenvalues"]))],
                    y=results["eigenvalues"],
                    marker_color="steelblue",
                )
            ])
            
            fig.update_layout(
                title="Eigenvalue Spectrum",
                xaxis_title="Principal Component",
                yaxis_title="Eigenvalue",
                height=300,
                template="plotly_white",
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cumulative variance explained
            cumulative_var = np.cumsum(results["eigenvalues"]) / results["eigenvalues"].sum()
            
            fig = go.Figure(data=[
                go.Scatter(
                    x=[f"PC{i+1}" for i in range(len(cumulative_var))],
                    y=cumulative_var * 100,
                    mode="lines+markers",
                    marker_color="green",
                    line=dict(width=2),
                )
            ])
            
            fig.update_layout(
                title="Cumulative Variance Explained",
                xaxis_title="Principal Component",
                yaxis_title="Cumulative Variance (%)",
                height=300,
                template="plotly_white",
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Interpretation
        st.subheader("Interpretation")
        
        if avg_corr < 0.3:
            st.success(
                """
                🟢 **CALM REGIME**: Correlations are low, providing good diversification opportunities.
                - Assets moving independently
                - Diversification working well
                - Normal market conditions
                - **Action**: Maintain diversified portfolio
                """
            )
        elif avg_corr < 0.6:
            st.warning(
                """
                🟠 **STRESS REGIME**: Correlations rising, diversification deteriorating.
                - Assets beginning to move together
                - Market stress building
                - Increased systemic risk
                - **Action**: Consider risk reduction, increase hedges
                """
            )
        else:
            st.error(
                """
                🔴 **CRISIS REGIME**: Very high correlations, contagion risk.
                - All assets moving together (flight to quality)
                - Diversification breakdown
                - Systemic crisis conditions
                - **Action**: Defensive positioning, cash, quality assets only
                """
            )
    
    else:
        components.info_message("Click 'Analyze' with 'Correlation Regime' selected to analyze correlation dynamics.")



st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Macro Analysis powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
