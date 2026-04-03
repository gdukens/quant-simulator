#!/usr/bin/env python3
"""
Real Data Source Test - LITE MODE
Tests actual API connections to verify real data access
"""

import os
import requests
import yfinance as yf
from dotenv import load_dotenv
import json

def test_real_data_sources():
    """Test all configured real data sources"""
    load_dotenv()
    
    print(" REAL DATA SOURCES TEST")
    print("="*50)
    
    results = {'working': [], 'failed': []}
    
    # Test Yahoo Finance (no API key needed)
    print("\n Testing Yahoo Finance...")
    try:
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="5d", interval="1d")
        if len(data) > 0:
            latest_close = data['Close'].iloc[-1]
            print(f" Yahoo Finance: WORKING")
            print(f"   AAPL latest close: ${latest_close:.2f}")
            results['working'].append('Yahoo Finance')
        else:
            print(" Yahoo Finance: No data returned")
            results['failed'].append('Yahoo Finance')
    except Exception as e:
        print(f" Yahoo Finance: {e}")
        results['failed'].append('Yahoo Finance')
    
    # Test Alpha Vantage
    print("\n Testing Alpha Vantage...")
    try:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if api_key and len(api_key) > 10:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=MSFT&apikey={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                price = data['Global Quote']['05. price']
                print(f" Alpha Vantage: WORKING")
                print(f"   MSFT current price: ${float(price):.2f}")
                results['working'].append('Alpha Vantage')
            else:
                print(f" Alpha Vantage: {data.get('Error Message', 'API limit or error')}")
                results['failed'].append('Alpha Vantage')
        else:
            print(" Alpha Vantage: No API key configured")
            results['failed'].append('Alpha Vantage')
    except Exception as e:
        print(f" Alpha Vantage: {e}")
        results['failed'].append('Alpha Vantage')
    
    # Test FRED
    print("\n Testing FRED (Federal Reserve)...")
    try:
        api_key = os.getenv('FRED_API_KEY')
        if api_key:
            # Get 10-Year Treasury Rate
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GS10&api_key={api_key}&file_type=json&limit=1&sort_order=desc"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'observations' in data and len(data['observations']) > 0:
                rate = data['observations'][0]['value']
                date = data['observations'][0]['date']
                print(f" FRED: WORKING")
                print(f"   10-Year Treasury Rate: {rate}% (as of {date})")
                results['working'].append('FRED')
            else:
                print(" FRED: No data returned")
                results['failed'].append('FRED')
        else:
            print(" FRED: No API key configured")
            results['failed'].append('FRED')
    except Exception as e:
        print(f" FRED: {e}")
        results['failed'].append('FRED')
    
    # Summary
    print("\n" + "="*50)
    print(" REAL DATA STATUS SUMMARY:")
    
    if results['working']:
        print(f"\n WORKING DATA SOURCES ({len(results['working'])}):")
        for source in results['working']:
            print(f"   • {source}")
    
    if results['failed']:
        print(f"\n FAILED DATA SOURCES ({len(results['failed'])}):")
        for source in results['failed']:
            print(f"   • {source}")
    
    print(f"\n DATA MODE: {'REAL DATA' if results['working'] else 'FALLBACK TO DEMO'}")
    print(" STORAGE: LITE MODE (Redis cache + in-memory)")
    print(" CAPABILITIES: Live market data + historical analysis")
    
    return len(results['working']) > 0

if __name__ == "__main__":
    test_real_data_sources()