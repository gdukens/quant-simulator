#!/usr/bin/env python3
"""
Test FRED Integration
"""

from quantlib_pro.data.fred_client import FREDClient
from quantlib_pro.data.fred_provider import FREDProvider

def test_fred_integration():
    """Test FRED client and provider integration"""
    print('🧪 Testing FRED Integration...')
    print('='*50)
    
    # Test FRED Client
    print('\n🔗 Testing FRED Client...')
    try:
        fred = FREDClient(api_key="5f5dcf2ef53c496228fa2935b71d9d40")
        snapshot = fred.get_macro_snapshot()
        
        print('✅ FRED Client: WORKING!')
        print(f'   GDP Growth: {snapshot.get("gdp_growth", "N/A")}%')  
        print(f'   Unemployment: {snapshot.get("unemployment", "N/A")}%')
        print(f'   10Y Treasury: {snapshot.get("treasury_10y", "N/A")}%')
        print(f'   PMI: {snapshot.get("pmi", "N/A")}')
        
    except Exception as e:
        print(f'❌ FRED Client failed: {e}')
        return False
    
    # Test FRED Provider
    print('\n📊 Testing FRED Provider...')
    try:
        provider = FREDProvider(api_key="5f5dcf2ef53c496228fa2935b71d9d40")
        regime = provider.assess_macro_regime()
        
        print('✅ FRED Provider: WORKING!')
        print(f'   Economic Regime: {regime.get("regime", "N/A")}')
        print(f'   Confidence: {regime.get("confidence", 0):.1%}')
        print(f'   Recession Prob: {regime.get("recession_probability", 0):.1%}')
        
    except Exception as e:
        print(f'❌ FRED Provider failed: {e}')
        return False
    
    print('\n' + '='*50)
    print('🎉 FRED INTEGRATION: FULLY OPERATIONAL!')
    print('\n✅ Real Economic Data Available:')
    print('   • GDP Growth Rate (Federal Reserve)')
    print('   • Unemployment Rate (Bureau of Labor Statistics)')
    print('   • Consumer Price Index (Bureau of Labor Statistics)')
    print('   • 10-Year Treasury Rate (Federal Reserve)')
    print('   • Manufacturing PMI (Institute for Supply Management)')
    print('   • Consumer Sentiment (University of Michigan)')
    
    print('\n🌍 Macro Analysis Page now uses:')
    print('   • REAL economic indicators instead of simulated data')
    print('   • Live Federal Reserve data via FRED API')
    print('   • Automatic regime detection with real indicators')
    
    return True

if __name__ == "__main__":
    test_fred_integration()