"""
FRED Data Provider - Clean Implementation

Integrates FRED (Federal Reserve Economic Data) into the QuantLib Pro data architecture.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from quantlib_pro.data.fred_client import FREDClient

log = logging.getLogger(__name__)


class FREDProvider:
    """FRED data provider for economic indicators."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.fred = FREDClient(api_key=api_key)
    
    def get_economic_indicators(self, indicators: List[str], periods: int = 60) -> pd.DataFrame:
        """Fetch multiple economic indicators."""
        data = {}
        
        indicator_map = {
            'GDP_GROWTH': ('A191RL1Q225SBEA', 'quarterly'),
            'UNEMPLOYMENT': ('UNRATE', 'monthly'),
            'CPI': ('CPIAUCSL', 'monthly'),
            'FED_RATE': ('FEDFUNDS', 'monthly'),
            'PMI': ('NAPM', 'monthly'),
            'TREASURY_10Y': ('GS10', 'daily'),
        }
        
        for indicator in indicators:
            if indicator.upper() not in indicator_map:
                continue
                
            series_id, frequency = indicator_map[indicator.upper()]
            
            try:
                df = self.fred.get_series(series_id, limit=periods)
                if not df.empty:
                    data[indicator.upper()] = df['value']
            except Exception as e:
                log.error(f"Failed to fetch {indicator}: {e}")
        
        return pd.DataFrame(data)
    
    def get_macro_regime_data(self) -> Dict[str, float]:
        """Get current data for macro regime detection."""
        try:
            snapshot = self.fred.get_macro_snapshot()
            
            regime_data = {
                'gdp_growth': snapshot.get('gdp_growth', 2.5) or 2.5,
                'unemployment_rate': snapshot.get('unemployment', 4.0) or 4.0,
                'inflation_rate': snapshot.get('inflation', 3.0) or 3.0,
                'fed_funds_rate': snapshot.get('fed_funds_rate', 5.0) or 5.0,
                'treasury_10y': snapshot.get('treasury_10y', 4.5) or 4.5,
                'pmi': snapshot.get('pmi', 52.0) or 52.0,
                'consumer_sentiment': snapshot.get('consumer_sentiment', 100.0) or 100.0,
            }
            
            # Calculate yield spread
            try:
                treasury_2y, _ = self.fred.get_latest_value('GS2')
                regime_data['yield_spread'] = regime_data['treasury_10y'] - treasury_2y
            except:
                regime_data['yield_spread'] = 200
            
            return regime_data
            
        except Exception as e:
            log.error(f"FRED data unavailable: {e}")
            return {
                'gdp_growth': 2.5,
                'unemployment_rate': 4.0, 
                'inflation_rate': 3.0,
                'fed_funds_rate': 5.0,
                'treasury_10y': 4.5,
                'pmi': 52.0,
                'consumer_sentiment': 100.0,
                'yield_spread': 150,
            }
    
    def assess_macro_regime(self) -> Dict[str, any]:
        """Assess current macro economic regime."""
        data = self.get_macro_regime_data()
        
        expansion_score = 0
        recession_score = 0
        
        # GDP Growth
        gdp = data['gdp_growth']
        if gdp > 2.5:
            expansion_score += 0.3
        elif gdp < 0:
            recession_score += 0.4
        
        # Unemployment
        unemployment = data['unemployment_rate']
        if unemployment < 4.0:
            expansion_score += 0.2
        elif unemployment > 6.0:
            recession_score += 0.3
        
        # PMI
        pmi = data['pmi']
        if pmi > 52:
            expansion_score += 0.2
        elif pmi < 48:
            recession_score += 0.2
        
        # Yield Curve
        yield_spread = data['yield_spread']
        if yield_spread < 0:
            recession_score += 0.3
        elif yield_spread > 200:
            expansion_score += 0.1
        
        # Normalize probabilities
        total_score = expansion_score + recession_score
        if total_score > 0:
            expansion_prob = expansion_score / total_score
            recession_prob = recession_score / total_score
        else:
            expansion_prob = 0.5
            recession_prob = 0.5
        
        # Determine regime
        if expansion_prob > 0.6:
            regime = "Expansion"
            confidence = expansion_prob
        elif recession_prob > 0.6:
            regime = "Recession"
            confidence = recession_prob
        else:
            regime = "Transition"
            confidence = 1 - abs(expansion_prob - recession_prob)
        
        return {
            'regime': regime,
            'confidence': confidence,
            'expansion_probability': expansion_prob,
            'recession_probability': recession_prob,
            'indicators': data,
            'last_updated': datetime.now().isoformat(),
        }


def create_fred_provider(api_key: Optional[str] = None) -> FREDProvider:
    """Create FRED provider with optional API key."""
    return FREDProvider(api_key=api_key)