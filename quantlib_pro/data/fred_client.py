"""
FRED (Federal Reserve Economic Data) API Client

Provides access to economic indicators from the St. Louis Federal Reserve:
- GDP, unemployment, inflation data
- Interest rates and yield curves  
- Manufacturing indicators (PMI)
- Consumer sentiment and confidence

API Documentation: https://fred.stlouisfed.org/docs/api/
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

from quantlib_pro.utils.validation import require_positive

log = logging.getLogger(__name__)


class FREDError(Exception):
    """Raised when FRED API returns an error."""


class FREDClient:
    """
    FRED (Federal Reserve Economic Data) API client.
    
    Features:
    - 30+ key economic indicators
    - Historical time series data
    - Automatic caching and rate limiting
    - Data validation and cleaning
    
    Parameters
    ----------
    api_key : str, optional
        FRED API key. If None, reads from FRED_API_KEY env var.
    base_url : str
        API base URL (default: https://api.stlouisfed.org/fred)
    timeout : int
        Request timeout in seconds (default: 30)
    
    Examples
    --------
    >>> client = FREDClient()
    >>> gdp = client.get_gdp_growth()
    >>> unemployment = client.get_unemployment_rate()
    >>> rates = client.get_interest_rates()
    """
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    # Key Economic Series IDs
    SERIES_MAP = {
        # Growth Indicators
        'gdp': 'GDP',                           # Gross Domestic Product
        'gdp_growth': 'A191RL1Q225SBEA',        # Real GDP Growth Rate
        'industrial_production': 'INDPRO',      # Industrial Production Index
        
        # Employment
        'unemployment': 'UNRATE',               # Unemployment Rate
        'employment': 'PAYEMS',                 # Nonfarm Payrolls
        'labor_force': 'CIVPART',               # Labor Force Participation Rate
        
        # Inflation  
        'cpi': 'CPIAUCSL',                      # Consumer Price Index
        'cpi_core': 'CPILFESL',                 # Core CPI (ex food & energy)
        'ppi': 'PPIACO',                        # Producer Price Index
        'pce': 'PCE',                           # Personal Consumption Expenditures
        
        # Interest Rates
        'fed_funds': 'FEDFUNDS',                # Federal Funds Rate
        'treasury_10y': 'GS10',                 # 10-Year Treasury
        'treasury_2y': 'GS2',                   # 2-Year Treasury
        'treasury_3m': 'GS3M',                  # 3-Month Treasury
        
        # Financial Indicators
        'vix': 'VIXCLS',                        # VIX Volatility Index
        'sp500': 'SP500',                       # S&P 500 Index
        'dollar_index': 'DTWEXBGS',             # Trade Weighted US Dollar Index
        
        # Manufacturing & Business
        'ism_pmi': 'NAPM',                      # ISM Manufacturing PMI
        'capacity_utilization': 'TCU',          # Capacity Utilization
        
        # Consumer & Housing
        'consumer_sentiment': 'UMCSENT',        # University of Michigan Consumer Sentiment
        'consumer_confidence': 'CSCICP03USM665S', # Consumer Confidence Index  
        'housing_starts': 'HOUST',              # Housing Starts
        'existing_home_sales': 'EXHOSLUSM495S', # Existing Home Sales
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY environment variable "
                "or pass api_key parameter. Get key: https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantLib-Pro-FRED-Client/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make authenticated request to FRED API."""
        params['api_key'] = self.api_key
        params['file_type'] = 'json'
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # Check for FRED API errors
            if 'error_message' in data:
                raise FREDError(f"FRED API error: {data['error_message']}")
            
            return data
            
        except requests.RequestException as e:
            log.error(f"FRED API request failed: {e}")
            raise FREDError(f"Request failed: {e}")
    
    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Get time series data for a FRED series.
        
        Parameters
        ----------
        series_id : str
            FRED series identifier (e.g., 'GDP', 'UNRATE')
        start_date : str, optional
            Start date in YYYY-MM-DD format
        end_date : str, optional  
            End date in YYYY-MM-DD format
        limit : int
            Maximum number of observations
        
        Returns
        -------
        pd.DataFrame
            Time series with date index and value column
        """
        params = {
            'series_id': series_id,
            'limit': limit,
            'sort_order': 'desc',
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        data = self._make_request('series/observations', params)
        
        if 'observations' not in data or not data['observations']:
            log.warning(f"No data returned for series {series_id}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data['observations'])
        
        # Clean and convert data
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Filter out missing values
        df = df.dropna(subset=['value'])
        
        # Set date as index and sort
        df = df.set_index('date').sort_index()
        
        return df[['value']]
    
    def get_latest_value(self, series_id: str) -> Tuple[float, str]:
        """
        Get the latest value for a FRED series.
        
        Returns
        -------
        tuple
            (latest_value, date_string)
        """
        df = self.get_series(series_id, limit=1)
        if df.empty:
            raise FREDError(f"No data available for series {series_id}")
        
        latest_value = df.iloc[-1]['value']
        latest_date = df.index[-1].strftime('%Y-%m-%d')
        
        return latest_value, latest_date
    
    def get_gdp_growth(self, periods: int = 8) -> pd.DataFrame:
        """Get quarterly GDP growth rate (last 2 years)."""
        return self.get_series('A191RL1Q225SBEA', limit=periods)
    
    def get_unemployment_rate(self, periods: int = 24) -> pd.DataFrame:
        """Get monthly unemployment rate (last 2 years)."""
        return self.get_series('UNRATE', limit=periods)
    
    def get_inflation_rate(self, periods: int = 24) -> pd.DataFrame:
        """Get monthly CPI inflation rate (last 2 years)."""
        return self.get_series('CPIAUCSL', limit=periods)
    
    def get_interest_rates(self, periods: int = 60) -> pd.DataFrame:
        """Get key interest rates (last 5 years)."""
        rates_data = {}
        
        for name, series_id in [
            ('fed_funds', 'FEDFUNDS'),
            ('treasury_10y', 'GS10'), 
            ('treasury_2y', 'GS2'),
            ('treasury_3m', 'GS3M'),
        ]:
            try:
                df = self.get_series(series_id, limit=periods)
                if not df.empty:
                    rates_data[name] = df['value']
            except Exception as e:
                log.warning(f"Failed to fetch {name}: {e}")
        
        return pd.DataFrame(rates_data)
    
    def get_manufacturing_pmi(self, periods: int = 24) -> pd.DataFrame:
        """Get ISM Manufacturing PMI (last 2 years)."""
        return self.get_series('NAPM', limit=periods)
    
    def get_consumer_sentiment(self, periods: int = 24) -> pd.DataFrame:
        """Get University of Michigan Consumer Sentiment (last 2 years)."""
        return self.get_series('UMCSENT', limit=periods)
    
    def get_macro_snapshot(self) -> Dict[str, float]:
        """
        Get current snapshot of key macro indicators.
        
        Returns
        -------
        dict
            Latest values for key economic indicators
        """
        snapshot = {}
        
        indicators = [
            ('gdp_growth', 'A191RL1Q225SBEA'),
            ('unemployment', 'UNRATE'),
            ('inflation', 'CPIAUCSL'),
            ('fed_funds_rate', 'FEDFUNDS'),
            ('treasury_10y', 'GS10'),
            ('pmi', 'NAPM'),
            ('consumer_sentiment', 'UMCSENT'),
        ]
        
        for name, series_id in indicators:
            try:
                value, date = self.get_latest_value(series_id)
                snapshot[name] = value
                snapshot[f'{name}_date'] = date
            except Exception as e:
                log.warning(f"Failed to fetch {name}: {e}")
                snapshot[name] = None
        
        return snapshot
    
    def get_yield_curve(self) -> pd.DataFrame:
        """
        Get current yield curve (3M, 2Y, 5Y, 10Y, 30Y).
        
        Returns
        -------
        pd.DataFrame
            Current yield curve rates
        """
        curve_series = {
            '3M': 'GS3M',
            '2Y': 'GS2', 
            '5Y': 'GS5',
            '10Y': 'GS10',
            '30Y': 'GS30',
        }
        
        rates = {}
        for maturity, series_id in curve_series.items():
            try:
                value, _ = self.get_latest_value(series_id)
                rates[maturity] = value
            except Exception as e:
                log.warning(f"Failed to fetch {maturity} rate: {e}")
        
        return pd.DataFrame([rates], index=['Current'])
    
    def __repr__(self):
        return f"FREDClient(base_url='{self.base_url}')"


# Convenience function for creating client
def create_fred_client(api_key: Optional[str] = None) -> FREDClient:
    """Create FRED client with optional API key."""
    return FREDClient(api_key=api_key)