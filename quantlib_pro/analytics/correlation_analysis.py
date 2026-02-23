"""
Dynamic Correlation Analysis and Regime Detection.

Provides tools for:
- Rolling correlation analysis
- Correlation regime detection
- Correlation breakdown identification
- Dynamic Conditional Correlation (DCC) models
- Copula-based dependency analysis

Example
-------
>>> from quantlib_pro.analytics.correlation_analysis import CorrelationAnalyzer
>>>
>>> analyzer = CorrelationAnalyzer(returns_data)
>>> regimes = analyzer.detect_correlation_regimes()
>>> breakdown_events = analyzer.detect_correlation_breakdowns()
>>> rolling_corr = analyzer.calculate_rolling_correlation(window=60)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

log = logging.getLogger(__name__)


class CorrelationRegime(Enum):
    """Correlation market regimes."""
    LOW_CORRELATION = 'low_correlation'
    NORMAL_CORRELATION = 'normal_correlation'
    HIGH_CORRELATION = 'high_correlation'
    CRISIS = 'crisis'


@dataclass
class CorrelationBreakdown:
    """Correlation breakdown event."""
    date: pd.Timestamp
    severity: float
    avg_correlation_before: float
    avg_correlation_after: float
    affected_pairs: List[Tuple[str, str]]
    
    def __str__(self) -> str:
        return f"Breakdown on {self.date.date()}: {self.severity:.2%} increase (Δcorr={self.avg_correlation_after - self.avg_correlation_before:.2%})"


@dataclass
class RegimeChange:
    """Correlation regime change event."""
    date: pd.Timestamp
    from_regime: CorrelationRegime
    to_regime: CorrelationRegime
    confidence: float
    
    def __str__(self) -> str:
        return f"{self.date.date()}: {self.from_regime.value} → {self.to_regime.value} (confidence={self.confidence:.2%})"


class CorrelationAnalyzer:
    """
    Dynamic correlation analysis and regime detection.
    
    Analyzes correlation structure dynamics including:
    - Rolling correlations
    - Regime identification
    - Breakdown detection
    - Hierarchical clustering
    
    Parameters
    ----------
    returns : pd.DataFrame
        Asset returns (time × assets)
    window : int, optional
        Default rolling window for correlation
    """
    
    def __init__(
        self,
        returns: pd.DataFrame,
        window: int = 60,
    ):
        self.returns = returns
        self.window = window
        self.n_assets = len(returns.columns)
        
        # Calculate static correlation
        self.correlation_matrix = returns.corr()
        
        log.info(f"Initialized CorrelationAnalyzer: {self.n_assets} assets, {len(returns)} periods")
    
    def calculate_rolling_correlation(
        self,
        asset1: Optional[str] = None,
        asset2: Optional[str] = None,
        window: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Calculate rolling correlation.
        
        Parameters
        ----------
        asset1 : str, optional
            First asset (if None, calculates for all pairs)
        asset2 : str, optional
            Second asset
        window : int, optional
            Rolling window size
        
        Returns
        -------
        pd.DataFrame
            Rolling correlations (time × asset_pairs)
        """
        window = window or self.window
        
        if asset1 is not None and asset2 is not None:
            # Single pair
            corr = self.returns[[asset1, asset2]].rolling(window).corr().iloc[1::2, 0]
            return pd.DataFrame({f"{asset1}_{asset2}": corr})
        
        # All pairs
        rolling_corrs = {}
        
        for i, col1 in enumerate(self.returns.columns):
            for j, col2 in enumerate(self.returns.columns):
                if i < j:  # Upper triangle only
                    pair_name = f"{col1}_{col2}"
                    corr = self.returns[[col1, col2]].rolling(window).corr().iloc[1::2, 0]
                    corr.index = corr.index.droplevel(1)
                    rolling_corrs[pair_name] = corr
        
        return pd.DataFrame(rolling_corrs)
    
    def calculate_average_correlation(
        self,
        window: Optional[int] = None,
    ) -> pd.Series:
        """
        Calculate average pairwise correlation over time.
        
        Parameters
        ----------
        window : int, optional
            Rolling window size
        
        Returns
        -------
        pd.Series
            Average correlation time series
        """
        window = window or self.window
        
        log.info(f"Calculating average correlation with window={window}")
        
        # Calculate rolling correlation for each pair
        rolling_corrs = self.calculate_rolling_correlation(window=window)
        
        # Average across all pairs
        avg_corr = rolling_corrs.mean(axis=1)
        
        return avg_corr
    
    def detect_correlation_regimes(
        self,
        window: Optional[int] = None,
        n_regimes: int = 4,
    ) -> pd.Series:
        """
        Detect correlation regimes using k-means clustering.
        
        Parameters
        ----------
        window : int, optional
            Rolling window size
        n_regimes : int
            Number of regimes to detect
        
        Returns
        -------
        pd.Series
            Regime labels over time
        """
        window = window or self.window
        
        log.info(f"Detecting correlation regimes: n_regimes={n_regimes}")
        
        # Calculate average correlation
        avg_corr = self.calculate_average_correlation(window=window)
        avg_corr = avg_corr.dropna()
        
        # Use percentiles to define regimes
        percentiles = np.linspace(0, 100, n_regimes + 1)
        thresholds = np.percentile(avg_corr, percentiles)
        
        # Assign regimes
        regimes = pd.Series(index=avg_corr.index, dtype=object)
        
        regime_names = [
            CorrelationRegime.LOW_CORRELATION,
            CorrelationRegime.NORMAL_CORRELATION,
            CorrelationRegime.HIGH_CORRELATION,
            CorrelationRegime.CRISIS,
        ]
        
        for i in range(n_regimes):
            mask = (avg_corr >= thresholds[i]) & (avg_corr < thresholds[i + 1])
            if i < len(regime_names):
                regimes[mask] = regime_names[i]
            else:
                regimes[mask] = CorrelationRegime.CRISIS
        
        # Handle last bin
        regimes[avg_corr >= thresholds[-1]] = regime_names[-1]
        
        return regimes
    
    def detect_correlation_breakdowns(
        self,
        window: int = 60,
        lookback: int = 20,
        threshold: float = 0.2,
    ) -> List[CorrelationBreakdown]:
        """
        Detect correlation breakdown events (sudden increases).
        
        Parameters
        ----------
        window : int
            Rolling window for correlation
        lookback : int
            Lookback period for comparison
        threshold : float
            Minimum correlation increase to flag
        
        Returns
        -------
        list of CorrelationBreakdown
            Detected breakdown events
        """
        log.info(f"Detecting correlation breakdowns: threshold={threshold}")
        
        # Calculate average correlation
        avg_corr = self.calculate_average_correlation(window=window)
        avg_corr = avg_corr.dropna()
        
        # Calculate changes
        corr_change = avg_corr.diff(lookback)
        
        # Identify breakdowns
        breakdown_dates = corr_change[corr_change > threshold].index
        
        breakdowns = []
        for date in breakdown_dates:
            # Get before/after correlations
            before_date = avg_corr.index[avg_corr.index < date][-lookback] if len(avg_corr.index[avg_corr.index < date]) >= lookback else avg_corr.index[0]
            
            corr_before = avg_corr.loc[before_date]
            corr_after = avg_corr.loc[date]
            
            # Find affected pairs
            rolling_corrs = self.calculate_rolling_correlation(window=window)
            
            affected_pairs = []
            for col in rolling_corrs.columns:
                try:
                    before_val = rolling_corrs.loc[before_date, col]
                    after_val = rolling_corrs.loc[date, col]
                    
                    if after_val - before_val > threshold * 0.8:
                        # Parse pair name
                        asset1, asset2 = col.split('_', 1)
                        affected_pairs.append((asset1, asset2))
                except (KeyError, ValueError):
                    continue
            
            breakdowns.append(CorrelationBreakdown(
                date=date,
                severity=corr_change.loc[date],
                avg_correlation_before=corr_before,
                avg_correlation_after=corr_after,
                affected_pairs=affected_pairs,
            ))
        
        log.info(f"Detected {len(breakdowns)} correlation breakdowns")
        
        return breakdowns
    
    def detect_regime_changes(
        self,
        window: Optional[int] = None,
    ) -> List[RegimeChange]:
        """
        Detect correlation regime changes.
        
        Parameters
        ----------
        window : int, optional
            Rolling window size
        
        Returns
        -------
        list of RegimeChange
            Detected regime changes
        """
        regimes = self.detect_correlation_regimes(window=window)
        
        changes = []
        prev_regime = None
        
        for date, regime in regimes.items():
            if prev_regime is not None and regime != prev_regime:
                changes.append(RegimeChange(
                    date=date,
                    from_regime=prev_regime,
                    to_regime=regime,
                    confidence=0.8,  # Placeholder
                ))
            
            prev_regime = regime
        
        log.info(f"Detected {len(changes)} regime changes")
        
        return changes
    
    def calculate_hierarchical_clustering(
        self,
        method: str = 'ward',
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform hierarchical clustering on correlation matrix.
        
        Parameters
        ----------
        method : str
            Linkage method ('ward', 'complete', 'average', 'single')
        
        Returns
        -------
        tuple of (linkage_matrix, dendrogram_dict)
            Hierarchical clustering results
        """
        log.info(f"Calculating hierarchical clustering: method={method}")
        
        # Convert correlation to distance
        distance = 1 - self.correlation_matrix.abs()
        
        # Ensure symmetric
        distance = (distance + distance.T) / 2
        
        # Convert to condensed distance matrix
        condensed_dist = squareform(distance.values, checks=False)
        
        # Perform hierarchical clustering
        linkage_matrix = linkage(condensed_dist, method=method)
        
        # Generate dendrogram (without plotting)
        dend = dendrogram(linkage_matrix, no_plot=True)
        
        return linkage_matrix, dend
    
    def calculate_portfolio_correlation_risk(
        self,
        weights: np.ndarray,
    ) -> Dict[str, float]:
        """
        Calculate correlation risk metrics for a portfolio.
        
        Parameters
        ----------
        weights : np.ndarray
            Portfolio weights
        
        Returns
        -------
        dict
            Correlation risk metrics
        """
        # Average correlation weighted by portfolio weights
        weighted_corr = 0.0
        total_weight_product = 0.0
        
        for i, w_i in enumerate(weights):
            for j, w_j in enumerate(weights):
                if i != j:
                    corr = self.correlation_matrix.iloc[i, j]
                    weighted_corr += w_i * w_j * corr
                    total_weight_product += w_i * w_j
        
        avg_weighted_corr = weighted_corr / total_weight_product if total_weight_product > 0 else 0
        
        # Effective number of assets (diversification ratio)
        portfolio_var = weights @ self.correlation_matrix @ weights
        sum_individual_vars = np.sum(weights ** 2)
        
        effective_n = sum_individual_vars / portfolio_var if portfolio_var > 0 else 1
        
        # Concentration (max pairwise correlation)
        max_corr = 0.0
        max_pair = ('', '')
        
        for i in range(len(weights)):
            for j in range(i + 1, len(weights)):
                corr = abs(self.correlation_matrix.iloc[i, j])
                if weights[i] * weights[j] > 0 and corr > max_corr:
                    max_corr = corr
                    max_pair = (
                        self.correlation_matrix.index[i],
                        self.correlation_matrix.columns[j],
                    )
        
        return {
            'avg_weighted_correlation': avg_weighted_corr,
            'effective_n_assets': effective_n,
            'max_pairwise_correlation': max_corr,
            'max_correlation_pair': max_pair,
        }
    
    def calculate_correlation_distribution(
        self,
    ) -> Dict[str, float]:
        """
        Calculate statistics of correlation distribution.
        
        Returns
        -------
        dict
            Correlation distribution statistics
        """
        # Get upper triangle (exclude diagonal)
        corr_values = []
        
        for i in range(self.n_assets):
            for j in range(i + 1, self.n_assets):
                corr_values.append(self.correlation_matrix.iloc[i, j])
        
        corr_values = np.array(corr_values)
        
        return {
            'mean': np.mean(corr_values),
            'median': np.median(corr_values),
            'std': np.std(corr_values),
            'min': np.min(corr_values),
            'max': np.max(corr_values),
            'q25': np.percentile(corr_values, 25),
            'q75': np.percentile(corr_values, 75),
            'skewness': stats.skew(corr_values),
            'kurtosis': stats.kurtosis(corr_values),
        }
