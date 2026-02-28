"""
Options Manager - Options pricing and Greeks calculation tools.

This module provides comprehensive options pricing functionality including
Black-Scholes, Monte Carlo, and Greeks calculations for the QuantLib Pro SDK.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
import logging
from scipy.stats import norm
from scipy.optimize import brentq

logger = logging.getLogger(__name__)


class OptionsManager:
    """
    Options pricing and Greeks calculation tools.
    
    Provides functionality for:
    - Black-Scholes options pricing
    - Monte Carlo simulation pricing
    - Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
    - Implied volatility calculation
    - Option strategies analysis
    """
    
    def __init__(self, config=None):
        """
        Initialize Options Manager.
        
        Args:
            config: SDK configuration object
        """
        self.config = config
        self.risk_free_rate = getattr(config, 'risk_free_rate', 0.02) if config else 0.02
        logger.info("Options Manager initialized")
    
    def black_scholes(self, S: float, K: float, T: float, r: float = None, 
                     sigma: float = 0.2, option_type: str = "call") -> float:
        """
        Calculate Black-Scholes option price.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate (defaults to config value)
            sigma: Volatility
            option_type: "call" or "put"
            
        Returns:
            Option price
        """
        if r is None:
            r = self.risk_free_rate
            
        if T <= 0:
            # At expiration
            if option_type.lower() == "call":
                return max(S - K, 0)
            else:
                return max(K - S, 0)
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type.lower() == "call":
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type.lower() == "put":
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        logger.info(f"Calculated {option_type} option price: {price:.4f}")
        return float(price)
    
    def calculate_greeks(self, S: float, K: float, T: float, r: float = None,
                        sigma: float = 0.2, option_type: str = "call") -> Dict[str, float]:
        """
        Calculate option Greeks.
        
        Args:
            S: Current stock price
            K: Strike price  
            T: Time to expiration (in years)
            r: Risk-free rate (defaults to config value)
            sigma: Volatility
            option_type: "call" or "put"
            
        Returns:
            Dict containing Delta, Gamma, Theta, Vega, and Rho
        """
        if r is None:
            r = self.risk_free_rate
            
        if T <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Common terms
        sqrt_T = np.sqrt(T)
        exp_minus_rT = np.exp(-r * T)
        
        # Delta
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Gamma (same for calls and puts)
        gamma = norm.pdf(d1) / (S * sigma * sqrt_T)
        
        # Theta
        theta_part1 = -(S * norm.pdf(d1) * sigma) / (2 * sqrt_T)
        if option_type.lower() == "call":
            theta_part2 = -r * K * exp_minus_rT * norm.cdf(d2)
            theta = (theta_part1 + theta_part2) / 365  # Per day
        else:
            theta_part2 = r * K * exp_minus_rT * norm.cdf(-d2)
            theta = (theta_part1 + theta_part2) / 365  # Per day
        
        # Vega (same for calls and puts)
        vega = S * norm.pdf(d1) * sqrt_T / 100  # Per 1% vol change
        
        # Rho
        if option_type.lower() == "call":
            rho = K * T * exp_minus_rT * norm.cdf(d2) / 100  # Per 1% rate change
        else:
            rho = -K * T * exp_minus_rT * norm.cdf(-d2) / 100  # Per 1% rate change
        
        greeks = {
            "delta": float(delta),
            "gamma": float(gamma), 
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho)
        }
        
        logger.info(f"Calculated Greeks for {option_type} option")
        return greeks
    
    def implied_volatility(self, market_price: float, S: float, K: float, 
                          T: float, r: float = None, option_type: str = "call") -> float:
        """
        Calculate implied volatility from market price.
        
        Args:
            market_price: Market price of the option
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate (defaults to config value)
            option_type: "call" or "put"
            
        Returns:
            Implied volatility
        """
        if r is None:
            r = self.risk_free_rate
            
        def price_diff(vol):
            return self.black_scholes(S, K, T, r, vol, option_type) - market_price
        
        try:
            # Use Brent's method to find implied vol
            implied_vol = brentq(price_diff, 0.001, 5.0, xtol=1e-6)
            logger.info(f"Calculated implied volatility: {implied_vol:.4f}")
            return float(implied_vol)
        except ValueError:
            logger.error("Could not calculate implied volatility - no solution found")
            return np.nan
    
    def monte_carlo_price(self, S: float, K: float, T: float, r: float = None,
                         sigma: float = 0.2, option_type: str = "call", 
                         num_simulations: int = 10000) -> Dict[str, float]:
        """
        Calculate option price using Monte Carlo simulation.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate (defaults to config value)
            sigma: Volatility
            option_type: "call" or "put"
            num_simulations: Number of Monte Carlo simulations
            
        Returns:
            Dict containing price, standard error, and confidence intervals
        """
        if r is None:
            r = self.risk_free_rate
            
        # Generate random stock price paths
        np.random.seed(42)  # For reproducibility
        Z = np.random.standard_normal(num_simulations)
        ST = S * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)
        
        # Calculate payoffs
        if option_type.lower() == "call":
            payoffs = np.maximum(ST - K, 0)
        elif option_type.lower() == "put":
            payoffs = np.maximum(K - ST, 0)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        # Discount payoffs
        discounted_payoffs = payoffs * np.exp(-r * T)
        
        # Calculate statistics
        price = np.mean(discounted_payoffs)
        std_error = np.std(discounted_payoffs) / np.sqrt(num_simulations)
        confidence_95 = 1.96 * std_error
        
        result = {
            "price": float(price),
            "standard_error": float(std_error),
            "confidence_interval_lower": float(price - confidence_95),
            "confidence_interval_upper": float(price + confidence_95),
            "num_simulations": num_simulations
        }
        
        logger.info(f"Monte Carlo price: {price:.4f} ± {confidence_95:.4f}")
        return result
    
    def option_strategy_analysis(self, legs: List[Dict[str, Any]], 
                               spot_range: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Analyze multi-leg option strategy.
        
        Args:
            legs: List of option legs, each containing:
                  {position: 1/-1, type: "call"/"put", strike: float, price: float}
            spot_range: Range of spot prices for P&L analysis
            
        Returns:
            Dict containing strategy analysis
        """
        if not legs:
            raise ValueError("At least one option leg required")
        
        # Default spot range around current prices
        if spot_range is None:
            strikes = [leg['strike'] for leg in legs]
            min_strike, max_strike = min(strikes), max(strikes)
            spot_range = np.linspace(min_strike * 0.8, max_strike * 1.2, 100)
        
        strategy_pnl = np.zeros(len(spot_range))
        total_premium = 0
        
        for leg in legs:
            position = leg['position']  # 1 for long, -1 for short
            option_type = leg['type']
            strike = leg['strike']
            premium = leg.get('price', 0)
            
            # Calculate intrinsic values across spot range
            if option_type.lower() == "call":
                intrinsic_values = np.maximum(spot_range - strike, 0)
            else:
                intrinsic_values = np.maximum(strike - spot_range, 0)
            
            # Add to strategy P&L
            strategy_pnl += position * intrinsic_values
            total_premium += position * premium
        
        # Subtract net premium paid
        strategy_pnl -= total_premium
        
        # Calculate key statistics
        max_profit = np.max(strategy_pnl)
        max_loss = np.min(strategy_pnl)
        breakeven_points = spot_range[np.where(np.diff(np.sign(strategy_pnl)))[0]]
        
        result = {
            "spot_prices": spot_range.tolist(),
            "pnl_profile": strategy_pnl.tolist(),
            "max_profit": float(max_profit),
            "max_loss": float(max_loss),
            "net_premium": float(total_premium),
            "breakeven_points": breakeven_points.tolist(),
            "num_legs": len(legs)
        }
        
        logger.info(f"Analyzed {len(legs)}-leg option strategy")
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of options manager.
        
        Returns:
            Dict containing health status
        """
        return {
            "status": "healthy", 
            "module": "options",
            "risk_free_rate": self.risk_free_rate,
            "capabilities": [
                "black_scholes_pricing",
                "greeks_calculation",
                "implied_volatility",
                "monte_carlo_pricing",
                "strategy_analysis"
            ]
        }