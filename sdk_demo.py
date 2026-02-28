#!/usr/bin/env python3
"""
QuantLib Pro SDK Demo

This script demonstrates how to use the QuantLib Pro SDK for quantitative finance analysis.
Run this script to see the SDK in action and verify everything is working correctly.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """Main demo function showcasing SDK capabilities."""
    print("🚀 QuantLib Pro SDK Demo")
    print("=" * 50)
    
    try:
        # Import the SDK
        from quantlib_pro import QuantLibSDK, SDKConfig
        
        # Create SDK configuration
        config = SDKConfig(
            enable_caching=True,
            log_level="INFO",
            default_confidence_level=0.05
        )
        
        # Initialize SDK
        print("\n📊 Initializing QuantLib Pro SDK...")
        sdk = QuantLibSDK(config)
        
        # Perform health check
        print("\n🔍 Performing SDK health check...")
        health_status = sdk.health_check()
        print(f"✅ SDK Status: {health_status.get('sdk_version', 'Unknown')}")
        
        # Component status
        for component, status in health_status.get("components", {}).items():
            status_icon = "✅" if status.get("status") == "healthy" else "⚠️"
            print(f"{status_icon} {component.capitalize()}: {status.get('status', 'unknown')}")
        
        # Demo 1: Portfolio Analysis
        print("\n" + "="*50)
        print("📈 Demo 1: Portfolio Analysis")
        print("="*50)
        
        # Create a sample portfolio
        symbols = ["AAPL", "GOOGL", "MSFT"]
        print(f"Creating portfolio with symbols: {symbols}")
        
        portfolio = sdk.portfolio.create_portfolio(symbols)
        print(f"✅ Portfolio created: {portfolio['portfolio_id']}")
        
        # Get sample data
        print("Fetching market data...")
        market_data = sdk.data.get_price_data(symbols, period="6m")
        print(f"✅ Retrieved data: {market_data.shape}")
        print(f"Date range: {market_data.index[0].date()} to {market_data.index[-1].date()}")
        
        # Calculate portfolio metrics
        print("Calculating portfolio metrics...")
        returns = sdk.portfolio.calculate_returns(market_data)
        metrics = sdk.portfolio.calculate_portfolio_metrics(returns)
        
        print("📊 Portfolio Performance:")
        print(f"   • Total Return: {metrics['total_return']:.2%}")
        print(f"   • Annualized Return: {metrics['annualized_return']:.2%}")
        print(f"   • Volatility: {metrics['volatility']:.2%}")
        print(f"   • Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"   • Max Drawdown: {metrics['max_drawdown']:.2%}")
        
        # Demo 2: Risk Analysis
        print("\n" + "="*50)
        print("⚠️  Demo 2: Risk Analysis")
        print("="*50)
        
        print("Calculating risk metrics...")
        risk_metrics = sdk.risk.calculate_portfolio_risk(market_data)
        
        print("🎯 Risk Metrics:")
        print(f"   • Portfolio Volatility: {risk_metrics['portfolio_volatility']:.2%}")
        print(f"   • VaR (95%): {risk_metrics['var_95']:.2%}")
        print(f"   • VaR (99%): {risk_metrics['var_99']:.2%}")
        print(f"   • CVaR (95%): {risk_metrics['cvar_95']:.2%}")
        print(f"   • Skewness: {risk_metrics['skewness']:.3f}")
        print(f"   • Kurtosis: {risk_metrics['kurtosis']:.3f}")
        
        # Perform stress test
        print("\nRunning stress test scenarios...")
        scenarios = {
            "Market Crash": -0.20,    # 20% market drop
            "Flash Crash": -0.10,     # 10% sudden drop
            "Interest Rate Shock": -0.05  # 5% rate shock impact
        }
        
        stress_results = sdk.risk.stress_test(returns, scenarios)
        print("💥 Stress Test Results:")
        for scenario, result in stress_results.items():
            print(f"   • {scenario}: {result['percentage_loss']:.2f}% loss")
        
        # Demo 3: Options Analysis
        print("\n" + "="*50)
        print("📋 Demo 3: Options Analysis")
        print("="*50)
        
        # Calculate Black-Scholes option price
        S, K, T, r, sigma = 100, 105, 0.25, 0.05, 0.2
        
        print(f"Option parameters: S={S}, K={K}, T={T}, r={r}, σ={sigma}")
        
        call_price = sdk.options.black_scholes(S, K, T, r, sigma, "call")
        put_price = sdk.options.black_scholes(S, K, T, r, sigma, "put")
        
        print(f"✅ Call Option Price: ${call_price:.4f}")
        print(f"✅ Put Option Price: ${put_price:.4f}")
        
        # Calculate Greeks
        print("Calculating option Greeks...")
        greeks = sdk.options.calculate_greeks(S, K, T, r, sigma, "call")
        
        print("📈 Option Greeks:")
        print(f"   • Delta: {greeks['delta']:.4f}")
        print(f"   • Gamma: {greeks['gamma']:.4f}")
        print(f"   • Theta: {greeks['theta']:.4f}")
        print(f"   • Vega: {greeks['vega']:.4f}")
        print(f"   • Rho: {greeks['rho']:.4f}")
        
        # Demo 4: Quick Analysis
        print("\n" + "="*50)
        print("⚡ Demo 4: Quick Analysis")
        print("="*50)
        
        print("Running quick analysis on tech stocks...")
        tech_stocks = ["AAPL", "MSFT", "GOOGL", "NVDA"]
        
        analysis = sdk.quick_analysis(tech_stocks, period="1y")
        
        if "error" not in analysis:
            print("✅ Analysis completed successfully!")
            print(f"   • Analysis timestamp: {analysis['analysis_timestamp']}")
            print(f"   • Symbols analyzed: {', '.join(analysis['symbols'])}")
            print(f"   • Period: {analysis['period']}")
        else:
            print(f"⚠️ Analysis error: {analysis['error']}")
        
        # Demo 5: Economic Data
        print("\n" + "="*50)
        print("🏛️  Demo 5: Economic Data")
        print("="*50)
        
        print("Retrieving economic indicators...")
        indicators = sdk.macro.get_economic_indicators()
        
        print("📊 Economic Indicators:")
        for indicator, value in indicators.items():
            print(f"   • {indicator.replace('_', ' ').title()}: {value}%")
        
        # Demo 6: Market Regime Detection
        print("\n" + "="*50)
        print("🔄 Demo 6: Market Regime Detection")
        print("="*50)
        
        print("Detecting market regime for SPY...")
        spy_data = sdk.data.get_price_data("SPY", period="3m")
        regime = sdk.market_regime.detect_regime(spy_data.iloc[:, 0])
        
        print(f"📈 Current Market Regime: {regime.replace('_', ' ').title()}")
        
        # Summary
        print("\n" + "="*50)
        print("🎉 SDK Demo Completed Successfully!")
        print("="*50)
        
        print(f"""
✅ All demos completed successfully!

🚀 SDK Features Demonstrated:
   • Portfolio creation and analysis
   • Risk metrics and stress testing
   • Options pricing and Greeks
   • Economic data retrieval
   • Market regime detection
   • Quick analysis capabilities

📦 Ready for production use or further development!

💡 Next Steps:
   • Explore individual modules in depth
   • Customize SDK configuration
   • Build your own quantitative strategies
   • Integrate with your existing workflows
        """)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure QuantLib Pro is properly installed.")
        return False
        
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        print("Please check your installation and try again.")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'numpy', 'pandas', 'scipy', 'matplotlib'
    ]
    
    optional_packages = [
        'yfinance', 'scikit-learn', 'plotly'
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} (required)")
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} (optional)")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + ' '.join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Install with: pip install " + ' '.join(missing_optional))
    
    print("✅ Dependencies check completed!")
    return True

if __name__ == "__main__":
    print("QuantLib Pro SDK Demo")
    print("Version: 1.0.0")
    print("Author: QuantLib Pro Team")
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing required dependencies before running the demo.")
        sys.exit(1)
    
    print()
    
    # Run the main demo
    success = main()
    
    if success:
        print("\n🎯 Demo completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Demo failed. Please check the error messages above.")
        sys.exit(1)