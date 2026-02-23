"""
Options Pricing Dashboard

Week 12: Streamlit page for options pricing, Greeks analysis, and volatility surface.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

from quantlib_pro.ui import components
from quantlib_pro.options.black_scholes import price_with_greeks, implied_volatility
from quantlib_pro.options.monte_carlo import price_european

# Page config
st.set_page_config(
    page_title="Options Pricing - QuantLib Pro",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Options Pricing")
st.markdown("Price European options using Black-Scholes and Monte Carlo methods, analyze Greeks, and visualize payoffs.")

# Initialize session state
if "option_results" not in st.session_state:
    st.session_state.option_results = None

# Sidebar controls
with st.sidebar:
    st.header("Option Parameters")
    
    # Option type
    option_type = st.selectbox(
        "Option Type",
        ["call", "put"],
        index=0,
    )
    
    # Underlying parameters
    st.subheader("Underlying Asset")
    
    spot_price = st.number_input(
        "Spot Price ($)",
        min_value=1.0,
        max_value=10000.0,
        value=100.0,
        step=1.0,
    )
    
    strike_price = st.number_input(
        "Strike Price ($)",
        min_value=1.0,
        max_value=10000.0,
        value=100.0,
        step=1.0,
    )
    
    # Time parameters
    st.subheader("Time & Rates")
    
    days_to_expiry = st.slider(
        "Days to Expiration",
        min_value=1,
        max_value=365*2,
        value=30,
        step=1,
    )
    time_to_expiry = days_to_expiry / 365.0
    
    risk_free_rate = st.slider(
        "Risk-free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.1,
    ) / 100
    
    dividend_yield = st.slider(
        "Dividend Yield (%)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
    ) / 100
    
    # Volatility
    st.subheader("Volatility")
    
    volatility = st.slider(
        "Implied Volatility (%)",
        min_value=1.0,
        max_value=200.0,
        value=20.0,
        step=1.0,
    ) / 100
    
    # Pricing method
    st.subheader("Pricing Method")
    
    pricing_method = st.selectbox(
        "Method",
        ["Black-Scholes", "Monte Carlo"],
        index=0,
    )
    
    if pricing_method == "Monte Carlo":
        num_simulations = st.number_input(
            "Number of Simulations",
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=10000,
        )
        
        num_steps = st.number_input(
            "Time Steps",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
        )
    
    # Price button
    price_button = st.button("💰 Price Option", type="primary", use_container_width=True)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["💰 Pricing", "📈 Greeks", "📊 Payoff Diagram", "🔍 Implied Vol"])

with tab1:
    st.header("Option Pricing")
    
    if price_button:
        with st.spinner(f"Pricing using {pricing_method}..."):
            try:
                if pricing_method == "Black-Scholes":
                    # Black-Scholes pricing
                    result = price_with_greeks(
                        spot=spot_price,
                        strike=strike_price,
                        T=time_to_expiry,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=option_type,
                        q=dividend_yield,
                    )
                    
                    option_price = result["price"]
                    greeks = {
                        "Delta": result["delta"],
                        "Gamma": result["gamma"],
                        "Vega": result["vega"],
                        "Theta": result["theta"],
                        "Rho": result["rho"],
                    }
                    
                    st.session_state.option_results = {
                        "price": option_price,
                        "greeks": greeks,
                        "method": "Black-Scholes",
                        "option_type": option_type,
                        "spot": spot_price,
                        "strike": strike_price,
                        "time_to_expiry": time_to_expiry,
                        "volatility": volatility,
                        "risk_free_rate": risk_free_rate,
                        "dividend_yield": dividend_yield,
                    }
                    
                else:  # Monte Carlo
                    result = price_european(
                        S0=spot_price,
                        K=strike_price,
                        T=time_to_expiry,
                        r=risk_free_rate,
                        sigma=volatility,
                        option_type=option_type,
                        n_paths=int(num_simulations),
                        n_steps=int(num_steps),
                    )
                    
                    option_price = result["option_price"]
                    
                    st.session_state.option_results = {
                        "price": option_price,
                        "confidence_interval": result.get("confidence_interval_95"),
                        "standard_error": result.get("standard_error"),
                        "num_simulations": num_simulations,
                        "method": "Monte Carlo",
                        "option_type": option_type,
                        "spot": spot_price,
                        "strike": strike_price,
                        "time_to_expiry": time_to_expiry,
                        "volatility": volatility,
                        "risk_free_rate": risk_free_rate,
                    }
                
                components.success_message("Option priced successfully!")
                
            except Exception as e:
                components.error_message(f"Pricing failed: {str(e)}")
                st.session_state.option_results = None
    
    # Display pricing results
    if st.session_state.option_results:
        results = st.session_state.option_results
        
        # Main metrics
        intrinsic_value = max(
            (results["spot"] - results["strike"]) if results["option_type"] == "call" 
            else (results["strike"] - results["spot"]),
            0
        )
        time_value = results["price"] - intrinsic_value
        
        moneyness = results["spot"] / results["strike"]
        if moneyness > 1.05:
            moneyness_label = "ITM (In-the-Money)" if results["option_type"] == "call" else "OTM (Out-of-the-Money)"
        elif moneyness < 0.95:
            moneyness_label = "OTM (Out-of-the-Money)" if results["option_type"] == "call" else "ITM (In-the-Money)"
        else:
            moneyness_label = "ATM (At-the-Money)"
        
        components.multi_metric_row([
            {
                "title": "Option Price",
                "value": f"${results['price']:.2f}",
                "help": f"{results['option_type'].upper()} option price using {results['method']}",
            },
            {
                "title": "Intrinsic Value",
                "value": f"${intrinsic_value:.2f}",
                "help": "Value if exercised immediately",
            },
            {
                "title": "Time Value",
                "value": f"${time_value:.2f}",
                "help": "Premium above intrinsic value",
            },
            {
                "title": "Moneyness",
                "value": moneyness_label,
                "help": f"S/K = {moneyness:.3f}",
            },
        ])
        
        st.markdown("---")
        
        # Detailed parameters
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Input Parameters")
            params_df = pd.DataFrame({
                "Parameter": [
                    "Option Type",
                    "Spot Price",
                    "Strike Price",
                    "Time to Expiry",
                    "Volatility",
                    "Risk-free Rate",
                ],
                "Value": [
                    results["option_type"].upper(),
                    f"${results['spot']:.2f}",
                    f"${results['strike']:.2f}",
                    f"{results['time_to_expiry']*365:.0f} days ({results['time_to_expiry']:.4f} years)",
                    f"{results['volatility']*100:.2f}%",
                    f"{results['risk_free_rate']*100:.2f}%",
                ],
            })
            
            if "dividend_yield" in results:
                params_df = pd.concat([
                    params_df,
                    pd.DataFrame({
                        "Parameter": ["Dividend Yield"],
                        "Value": [f"{results['dividend_yield']*100:.2f}%"],
                    })
                ])
            
            st.dataframe(params_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Pricing Details")
            details_df = pd.DataFrame({
                "Metric": ["Method", "Price", "Intrinsic Value", "Time Value"],
                "Value": [
                    results["method"],
                    f"${results['price']:.4f}",
                    f"${intrinsic_value:.4f}",
                    f"${time_value:.4f}",
                ],
            })
            
            if results["method"] == "Monte Carlo":
                ci = results.get("confidence_interval", [0, 0])
                details_df = pd.concat([
                    details_df,
                    pd.DataFrame({
                        "Metric": ["Simulations", "Std Error", "95% CI Lower", "95% CI Upper"],
                        "Value": [
                            f"{results['num_simulations']:,}",
                            f"${results.get('standard_error', 0):.4f}",
                            f"${ci[0]:.4f}" if isinstance(ci, (list, tuple)) else "N/A",
                            f"${ci[1]:.4f}" if isinstance(ci, (list, tuple)) else "N/A",
                        ],
                    })
                ])
            
            st.dataframe(details_df, hide_index=True, use_container_width=True)
        
    else:
        components.info_message("Click 'Price Option' to calculate the option value.")

with tab2:
    st.header("Option Greeks")
    
    if st.session_state.option_results and "greeks" in st.session_state.option_results:
        greeks = st.session_state.option_results["greeks"]
        
        # Plot Greeks
        fig = components.plot_greeks(greeks, height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        # Greeks explanation
        st.subheader("Greeks Interpretation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                f"""
                **Delta ({greeks['Delta']:.4f})**  
                Change in option price for $1 change in underlying.  
                _{abs(greeks['Delta'])*100:.2f}% hedge ratio_
                
                **Gamma ({greeks['Gamma']:.4f})**  
                Rate of change of Delta.  
                _Measures Delta stability_
                
                **Vega ({greeks['Vega']:.4f})**  
                Change in option price for 1% change in volatility.  
                _${abs(greeks['Vega']):.2f} per 1% vol change_
                """
            )
        
        with col2:
            st.markdown(
                f"""
                **Theta ({greeks['Theta']:.4f})**  
                Daily time decay of option value.  
                _${abs(greeks['Theta']):.2f} per day_
                
                **Rho ({greeks['Rho']:.4f})**  
                Change in option price for 1% change in interest rate.  
                _${abs(greeks['Rho']):.2f} per 1% rate change_
                """
            )
        
        # Sensitivity analysis
        st.subheader("Sensitivity Analysis")
        
        spot_range = np.linspace(spot_price * 0.7, spot_price * 1.3, 50)
        option_values = []
        deltas = []
        
        for S in spot_range:
            result = price_with_greeks(
                spot=S,
                strike=strike_price,
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=volatility,
                option_type=option_type,
                q=dividend_yield if "dividend_yield" in st.session_state.option_results else 0,
            )
            option_values.append(result["price"])
            deltas.append(result["delta"])
        
        sensitivity_df = pd.DataFrame({
            "Spot Price": spot_range,
            "Option Value": option_values,
            "Delta": deltas,
        })
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Option Value vs. Spot Price", "Delta vs. Spot Price"),
            vertical_spacing=0.15,
        )
        
        fig.add_trace(
            go.Scatter(x=sensitivity_df["Spot Price"], y=sensitivity_df["Option Value"],
                      mode="lines", name="Option Value", line=dict(color="steelblue")),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=sensitivity_df["Spot Price"], y=sensitivity_df["Delta"],
                      mode="lines", name="Delta", line=dict(color="orange")),
            row=2, col=1
        )
        
        fig.add_vline(x=spot_price, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_vline(x=spot_price, line_dash="dash", line_color="red", row=2, col=1)
        
        fig.update_xaxes(title_text="Spot Price ($)", row=2, col=1)
        fig.update_yaxes(title_text="Option Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Delta", row=2, col=1)
        
        fig.update_layout(height=600, template="plotly_white", showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif st.session_state.option_results:
        components.warning_message("Greeks are only available for Black-Scholes pricing.")
    else:
        components.info_message("Price option using Black-Scholes to see Greeks.")

with tab3:
    st.header("Payoff Diagram")
    
    # Generate payoff diagram
    spot_range = np.linspace(max(strike_price * 0.5, 1), strike_price * 1.5, 100)
    
    if option_type == "call":
        payoff_intrinsic = np.maximum(spot_range - strike_price, 0)
    else:  # put
        payoff_intrinsic = np.maximum(strike_price - spot_range, 0)
    
    if st.session_state.option_results:
        option_price = st.session_state.option_results["price"]
        payoff_net = payoff_intrinsic - option_price
    else:
        option_price = 0
        payoff_net = payoff_intrinsic
    
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Intrinsic value at expiration
    fig.add_trace(go.Scatter(
        x=spot_range,
        y=payoff_intrinsic,
        mode="lines",
        name="Payoff at Expiration",
        line=dict(color="steelblue", width=2),
    ))
    
    if st.session_state.option_results:
        # Net profit/loss
        fig.add_trace(go.Scatter(
            x=spot_range,
            y=payoff_net,
            mode="lines",
            name="Net P&L (incl. premium)",
            line=dict(color="green", width=2, dash="dash"),
        ))
    
    # Breakeven and strike lines
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=strike_price, line_dash="dash", line_color="red",
                  annotation_text=f"Strike: ${strike_price:.2f}", annotation_position="top")
    
    if st.session_state.option_results:
        if option_type == "call":
            breakeven = strike_price + option_price
        else:
            breakeven = strike_price - option_price
        
        fig.add_vline(x=breakeven, line_dash="dash", line_color="orange",
                      annotation_text=f"B/E: ${breakeven:.2f}", annotation_position="bottom")
    
    fig.update_layout(
        title=f"{option_type.upper()} Option Payoff Diagram",
        xaxis_title="Spot Price at Expiration ($)",
        yaxis_title="Profit/Loss ($)",
        height=500,
        template="plotly_white",
        hovermode="x unified",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Payoff table
    if st.session_state.option_results:
        st.subheader("Key Levels")
        
        if option_type == "call":
            breakeven = strike_price + option_price
            max_loss = option_price
            max_profit = "Unlimited"
        else:
            breakeven = strike_price - option_price
            max_loss = option_price
            max_profit = f"${strike_price - option_price:.2f}"
        
        levels_df = pd.DataFrame({
            "Metric": ["Strike Price", "Breakeven", "Max Loss", "Max Profit", "Premium Paid"],
            "Value": [
                f"${strike_price:.2f}",
                f"${breakeven:.2f}",
                f"${max_loss:.2f}",
                max_profit,
                f"${option_price:.2f}",
            ],
        })
        
        st.dataframe(levels_df, hide_index=True, use_container_width=True)

with tab4:
    st.header("Implied Volatility Calculator")
    
    st.markdown("Calculate implied volatility from observed option prices.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        observed_price = st.number_input(
            "Observed Option Price ($)",
            min_value=0.01,
            max_value=spot_price,
            value=10.0 if not st.session_state.option_results else st.session_state.option_results["price"],
            step=0.01,
        )
    
    with col2:
        initial_guess = st.slider(
            "Initial Volatility Guess (%)",
            min_value=1,
            max_value=200,
            value=20,
            step=1,
        ) / 100
    
    calc_iv_button = st.button("Calculate Implied Vol")
    
    if calc_iv_button:
        with st.spinner("Calculating implied volatility..."):
            try:
                iv_result = implied_volatility(
                    option_price=observed_price,
                    spot=spot_price,
                    strike=strike_price,
                    T=time_to_expiry,
                    r=risk_free_rate,
                    option_type=option_type,
                    q=dividend_yield,
                    initial_guess=initial_guess,
                )
                
                components.success_message("Implied volatility calculated!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Implied Volatility", f"{iv_result['implied_volatility']*100:.2f}%")
                
                with col2:
                    st.metric("Iterations", iv_result.get("iterations", "N/A"))
                
                with col3:
                    error = iv_result.get("convergence_error", 0)
                    st.metric("Error", f"${error:.4f}")
                
                # Compare with input volatility
                if abs(iv_result['implied_volatility'] - volatility) > 0.01:
                    st.info(
                        f"ℹ️ Implied vol ({iv_result['implied_volatility']*100:.2f}%) differs from "
                        f"input vol ({volatility*100:.2f}%). This is expected if observed price ≠ theoretical price."
                    )
                
            except Exception as e:
                components.error_message(f"Failed to calculate implied volatility: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    Options Pricing powered by QuantLib Pro
    </div>
    """,
    unsafe_allow_html=True,
)
