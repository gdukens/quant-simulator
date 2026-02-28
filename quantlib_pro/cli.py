#!/usr/bin/env python3
"""
QuantLib Pro Command Line Interface

This module provides command-line access to QuantLib Pro SDK functionality.
"""

import sys
import argparse
import json
from typing import Dict, Any, List, Optional
import logging

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def cmd_demo(args):
    """Run the SDK demo."""
    print("🚀 Running QuantLib Pro SDK Demo...")
    try:
        import subprocess
        import os
        
        # Find demo script path
        demo_path = os.path.join(os.path.dirname(__file__), "..", "sdk_demo.py")
        if not os.path.exists(demo_path):
            # Try alternative paths
            demo_path = "sdk_demo.py"
        
        result = subprocess.run([sys.executable, demo_path], 
                              capture_output=args.quiet, text=True)
        
        if result.returncode == 0:
            print("✅ Demo completed successfully!")
        else:
            print("❌ Demo failed!")
            if result.stderr:
                print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Failed to run demo: {e}")

def cmd_health(args):
    """Check SDK health status."""
    print("🔍 Checking QuantLib Pro SDK Health...")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        health_status = sdk.health_check()
        
        print(f"✅ SDK Version: {health_status.get('sdk_version', 'Unknown')}")
        
        # Check components
        components = health_status.get("components", {})
        healthy_count = 0
        total_count = len(components)
        
        for component, status in components.items():
            is_healthy = status.get("status") == "healthy"
            status_icon = "✅" if is_healthy else "⚠️"
            print(f"{status_icon} {component.capitalize()}: {status.get('status', 'unknown')}")
            
            if is_healthy:
                healthy_count += 1
        
        print(f"\n📊 Health Summary: {healthy_count}/{total_count} components healthy")
        
        if args.json:
            print("\nJSON Output:")
            print(json.dumps(health_status, indent=2))
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def cmd_data(args):
    """Get market data."""
    print(f"📊 Fetching data for: {', '.join(args.symbols)}")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        data = sdk.data.get_price_data(args.symbols, period=args.period)
        
        print(f"✅ Retrieved data: {data.shape}")
        print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
        
        if args.save:
            data.to_csv(args.save)
            print(f"💾 Data saved to: {args.save}")
        
        if not args.quiet:
            print("\nPreview (last 5 rows):")
            print(data.tail().to_string())
            
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")

def cmd_portfolio(args):
    """Portfolio operations."""
    print(f"📈 Portfolio operation: {args.action}")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        
        if args.action == "optimize":
            # Get data
            data = sdk.data.get_price_data(args.symbols, period="1y")
            returns = data.pct_change().dropna()
            
            # Calculate expected returns and covariance
            expected_returns = returns.mean() * 252
            cov_matrix = returns.cov() * 252
            
            # Optimize
            if args.method == "max_sharpe":
                result = sdk.portfolio.optimize_portfolio(
                    expected_returns, cov_matrix, risk_aversion=0.5
                )
                
                print("✅ Portfolio optimization completed!")
                print("Optimal weights:")
                for asset, weight in result['optimal_weights'].items():
                    print(f"   {asset}: {weight:.2%}")
                
                print(f"\nExpected Return: {result['expected_return']:.2%}")
                print(f"Expected Risk: {result['expected_risk']:.2%}")
                print(f"Sharpe Ratio: {result['sharpe_ratio']:.3f}")
                
            else:
                print(f"❌ Unknown optimization method: {args.method}")
        
        elif args.action == "analyze":
            # Portfolio analysis
            data = sdk.data.get_price_data(args.symbols, period="1y")
            returns = sdk.portfolio.calculate_returns(data)
            metrics = sdk.portfolio.calculate_portfolio_metrics(returns)
            
            print("✅ Portfolio analysis completed!")
            print(f"Total Return: {metrics['total_return']:.2%}")
            print(f"Annualized Return: {metrics['annualized_return']:.2%}")
            print(f"Volatility: {metrics['volatility']:.2%}")
            print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
            
        else:
            print(f"❌ Unknown portfolio action: {args.action}")
            
    except Exception as e:
        print(f"❌ Portfolio operation failed: {e}")

def cmd_risk(args):
    """Risk analysis operations."""
    print(f"⚠️  Risk analysis: {args.analysis_type}")
    
    try:
        from quantlib_pro import QuantLibSDK
        
        sdk = QuantLibSDK()
        
        if args.portfolio:
            # Load portfolio from file
            with open(args.portfolio, 'r') as f:
                portfolio_data = json.load(f)
                symbols = portfolio_data.get('symbols', [])
        else:
            symbols = ['SPY']  # Default to market
        
        # Get data
        data = sdk.data.get_price_data(symbols, period="1y")
        
        if args.analysis_type == "var":
            returns = sdk.portfolio.calculate_returns(data)
            var = sdk.risk.calculate_var(returns, confidence_level=args.confidence)
            
            print(f"✅ Value at Risk (VaR): {var:.2%}")
            print(f"Confidence Level: {args.confidence:.1%}")
            
        elif args.analysis_type == "stress":
            returns = sdk.portfolio.calculate_returns(data)
            scenarios = {
                "Market Crash": -0.20,
                "Flash Crash": -0.10,
                "Rate Shock": -0.05
            }
            
            results = sdk.risk.stress_test(returns, scenarios)
            
            print("✅ Stress test results:")
            for scenario, result in results.items():
                print(f"   {scenario}: {result['percentage_loss']:.2f}% loss")
        
        else:
            print(f"❌ Unknown risk analysis type: {args.analysis_type}")
            
    except Exception as e:
        print(f"❌ Risk analysis failed: {e}")

def cmd_version(args):
    """Show version information."""
    try:
        from quantlib_pro import __version__, __author__
        print(f"QuantLib Pro SDK v{__version__}")
        print(f"Author: {__author__}")
        
        if args.detailed:
            import sys
            import platform
            print(f"Python: {sys.version}")
            print(f"Platform: {platform.platform()}")
            
            # Check dependencies
            try:
                import numpy
                print(f"NumPy: {numpy.__version__}")
            except ImportError:
                pass
                
            try:
                import pandas
                print(f"Pandas: {pandas.__version__}")
            except ImportError:
                pass
                
    except Exception as e:
        print(f"❌ Version check failed: {e}")

def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="QuantLib Pro SDK Command Line Interface",
        prog="quantlib"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true",
        help="Suppress output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run SDK demonstration")
    demo_parser.set_defaults(func=cmd_demo)
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check SDK health")
    health_parser.add_argument("--json", action="store_true", help="Output JSON")
    health_parser.set_defaults(func=cmd_health)
    
    # Data command
    data_parser = subparsers.add_parser("data", help="Get market data")
    data_parser.add_argument("--symbols", required=True, help="Comma-separated symbols")
    data_parser.add_argument("--period", default="1y", help="Time period")
    data_parser.add_argument("--save", help="Save to CSV file")
    data_parser.set_defaults(func=cmd_data)
    
    # Portfolio command
    portfolio_parser = subparsers.add_parser("portfolio", help="Portfolio operations")
    portfolio_parser.add_argument("action", choices=["optimize", "analyze"])
    portfolio_parser.add_argument("--symbols", required=True, help="Comma-separated symbols")
    portfolio_parser.add_argument("--method", default="max_sharpe", help="Optimization method")
    portfolio_parser.set_defaults(func=cmd_portfolio)
    
    # Risk command
    risk_parser = subparsers.add_parser("risk", help="Risk analysis")
    risk_parser.add_argument("analysis_type", choices=["var", "stress"])
    risk_parser.add_argument("--portfolio", help="Portfolio JSON file")
    risk_parser.add_argument("--confidence", type=float, default=0.05, help="Confidence level")
    risk_parser.set_defaults(func=cmd_risk)
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument("--detailed", action="store_true", help="Show detailed info")
    version_parser.set_defaults(func=cmd_version)
    
    return parser

def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Parse symbols if provided
    if hasattr(args, 'symbols') and args.symbols:
        args.symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()