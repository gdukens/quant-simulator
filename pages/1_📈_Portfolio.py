"""
Portfolio Optimization Dashboard

Week 12: Streamlit page for portfolio optimization and efficient frontier analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import List, Dict

from quantlib_pro.ui import components
from quantlib_pro.portfolio.optimizer import PortfolioOptimizer
from quantlib_pro.data.market_data import MarketDataProvider

# Page config
st.set_page_config(
    page_title="Portfolio Optimization - QuantLib Pro",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Portfolio Optimization")
st.markdown("Optimize portfolio allocations using mean-variance optimization and visualize the efficient frontier.")

# Initialize session state
if "portfolio_results" not in st.session_state:
    st.session_state.portfolio_results = None

# Sidebar controls
with st.sidebar:
    st.header("Configuration")
    
    # Ticker selection
    st.subheader("Assets")
    ticker_input = st.text_area(
        "Enter tickers (one per line)",
        value="AAPL\nMSFT\nGOOG\nAMZN\nTSLA",
        height=150,
        help="Enter stock tickers separated by newlines",
    )
    tickers = [t.strip().upper() for t in ticker_input.split("\n") if t.strip()]
    
    st.markdown(f"**{len(tickers)} assets selected**")
    
    # Date range
    st.subheader("Date Range")
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    start_date = st.date_input(
        "Start Date",
        value=st.session_state.get("start_date", default_start),
    )
    end_date = st.date_input(
        "End Date",
        value=st.session_state.get("end_date", default_end),
    )
    
    # Optimization parameters
    st.subheader("Parameters")
    
    risk_free_rate = st.slider(
        "Risk-free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.get("risk_free_rate", 0.02) * 100,
        step=0.1,
    ) / 100
    
    target_return = st.slider(
        "Target Return (% annual)",
        min_value=0.0,
        max_value=50.0,
        value=15.0,
        step=1.0,
    ) / 100
    
    num_frontier_points = st.slider(
        "Frontier Points",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Number of portfolios to calculate for efficient frontier",
    )
    
    allow_short = st.checkbox(
        "Allow Short Selling",
        value=False,
        help="Allow negative weights (short positions)",
    )
    
    # Run optimization
    optimize_button = st.button("🚀 Optimize Portfolio", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Efficient Frontier", "💼 Optimal Weights", "📈 Performance"])

with tab1:
    st.header("Efficient Frontier")
    
    if optimize_button:
        with st.spinner("Fetching market data and optimizing..."):
            try:
                # Fetch market data
                data_provider = MarketDataProvider()
                
                # Use simulated data for demo
                dates = pd.date_range(start=start_date, end=end_date, freq="D")
                returns_data = {}
                
                for ticker in tickers:
                    # Simulate returns with different characteristics
                    np.random.seed(hash(ticker) % 2**32)
                    daily_returns = np.random.normal(0.0005, 0.02, len(dates))
                    returns_data[ticker] = daily_returns
                
                returns_df = pd.DataFrame(returns_data, index=dates)
                
                # Calculate efficient frontier
                optimizer = PortfolioOptimizer(risk_free_rate=risk_free_rate)
                
                # Generate frontier points
                min_return = returns_df.mean().min() * 252
                max_return = returns_df.mean().max() * 252
                target_returns = np.linspace(min_return, max_return, num_frontier_points)
                
                frontier_volatilities = []
                frontier_returns = []
                frontier_sharpe = []
                frontier_weights = []
                
                for target_ret in target_returns:
                    try:
                        result = optimizer.optimize(
                            returns=returns_df,
                            method="mean_variance",
                            target_return=target_ret,
                            allow_short=allow_short,
                        )
                        
                        frontier_returns.append(result["expected_return"])
                        frontier_volatilities.append(result["volatility"])
                        frontier_sharpe.append(result["sharpe_ratio"])
                        frontier_weights.append(result["weights"])
                    except:
                        continue
                
                # Find optimal portfolio (max Sharpe)
                optimal_idx = np.argmax(frontier_sharpe)
                
                # Store results
                st.session_state.portfolio_results = {
                    "returns": np.array(frontier_returns),
                    "volatilities": np.array(frontier_volatilities),
                    "sharpe_ratios": np.array(frontier_sharpe),
                    "weights": frontier_weights,
                    "optimal_idx": optimal_idx,
                    "tickers": tickers,
                    "returns_df": returns_df,
                }
                
                components.success_message("Optimization complete!")
                
            except Exception as e:
                components.error_message(f"Optimization failed: {str(e)}")
                st.session_state.portfolio_results = None
    
    # Display results
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        
        # Metrics
        optimal_idx = results["optimal_idx"]
        components.multi_metric_row([
            {
                "title": "Optimal Return",
                "value": f"{results['returns'][optimal_idx]*100:.2f}%",
                "help": "Expected annual return of optimal portfolio",
            },
            {
                "title": "Optimal Volatility",
                "value": f"{results['volatilities'][optimal_idx]*100:.2f}%",
                "help": "Annual volatility of optimal portfolio",
            },
            {
                "title": "Sharpe Ratio",
                "value": f"{results['sharpe_ratios'][optimal_idx]:.2f}",
                "help": "Risk-adjusted return metric",
            },
            {
                "title": "Portfolios Analyzed",
                "value": len(results['returns']),
                "help": "Number of efficient portfolios on frontier",
            },
        ])
        
        st.markdown("---")
        
        # Plot efficient frontier
        fig = components.plot_efficient_frontier(
            returns=results["returns"],
            volatilities=results["volatilities"],
            sharpe_ratios=results["sharpe_ratios"],
            optimal_idx=optimal_idx,
            height=600,
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Click 'Optimize Portfolio' to generate the efficient frontier.")

with tab2:
    st.header("Optimal Portfolio Weights")
    
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        optimal_idx = results["optimal_idx"]
        optimal_weights = results["weights"][optimal_idx]
        
        # Create weights dict
        weights_dict = dict(zip(results["tickers"], optimal_weights))
        
        # Display as pie chart
        fig = components.plot_portfolio_weights(weights_dict, height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display as table
        weights_df = pd.DataFrame({
            "Ticker": results["tickers"],
            "Weight": optimal_weights,
            "Weight (%)": optimal_weights * 100,
        }).sort_values("Weight", ascending=False)
        
        components.data_table(
            weights_df.style.format({"Weight": "{:.4f}", "Weight (%)": "{:.2f}%"}),
            title="Allocation Details",
        )
        
        # Download button
        csv = weights_df.to_csv(index=False)
        components.download_button(
            data=csv,
            filename="optimal_weights.csv",
            label="📥 Download Weights (CSV)",
        )
        
    else:
        components.info_message("Run optimization to see optimal portfolio weights.")

with tab3:
    st.header("Performance Analysis")
    
    if st.session_state.portfolio_results:
        results = st.session_state.portfolio_results
        returns_df = results["returns_df"]
        optimal_weights = results["weights"][results["optimal_idx"]]
        
        # Calculate portfolio returns
        portfolio_returns = (returns_df * optimal_weights).sum(axis=1)
        cumulative_returns = (1 + portfolio_returns).cumprod()
        
        # Plot cumulative returns
        perf_df = pd.DataFrame({
            "date": returns_df.index,
            "Cumulative Returns": cumulative_returns.values,
        })
        
        fig = components.plot_time_series(
            data=perf_df,
            title="Optimal Portfolio - Cumulative Returns",
            x_col="date",
            y_cols=["Cumulative Returns"],
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        st.subheader("Performance Metrics")
        
        total_return = (cumulative_returns.iloc[-1] - 1) * 100
        annualized_return = results["returns"][results["optimal_idx"]] * 100
        annualized_vol = results["volatilities"][results["optimal_idx"]] * 100
        sharpe = results["sharpe_ratios"][results["optimal_idx"]]
        max_drawdown = ((cumulative_returns / cumulative_returns.cummax()) - 1).min() * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Return", f"{total_return:.2f}%")
            st.metric("Annualized Return", f"{annualized_return:.2f}%")
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
        
        with col2:
            st.metric("Annualized Volatility", f"{annualized_vol:.2f}%")
            st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
            st.metric("Calendar Days", len(returns_df))
        
        # Correlation matrix
        st.subheader("Asset Correlation Matrix")
        corr_matrix = returns_df.corr()
        
        fig = components.plot_correlation_matrix(corr_matrix, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        components.info_message("Run optimization to see performance analysis.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Portfolio Optimization powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
