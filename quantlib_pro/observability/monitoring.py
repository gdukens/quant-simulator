"""
Performance Monitoring and Alerting System.

Provides real-time performance tracking, regression detection,
and alerting capabilities.

Example
-------
>>> from quantlib_pro.observability.monitoring import PerformanceMonitor, Alert
>>>
>>> monitor = PerformanceMonitor()
>>> monitor.add_baseline('calculate_var', target_duration_ms=100)
>>>
>>> # Monitoring context
>>> with monitor.track('calculate_var'):
>>>     result = calculate_var(returns)
>>>
>>> # Check for violations
>>> violations = monitor.get_violations()
>>> if violations:
>>>     for violation in violations:
>>>         print(f"ALERT: {violation}")
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class MetricType(Enum):
    """Types of performance metrics."""
    LATENCY = 'latency'
    THROUGHPUT = 'throughput'
    ERROR_RATE = 'error_rate'
    MEMORY = 'memory'
    CPU = 'cpu'


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison."""
    metric_name: str
    metric_type: MetricType
    target_value: float
    warning_threshold: float  # Percentage above target
    critical_threshold: float
    unit: str = 'ms'
    
    def check(self, value: float) -> Optional[Alert]:
        """Check if value violates baseline."""
        if value > self.target_value * (1 + self.critical_threshold):
            return Alert(
                level=AlertLevel.CRITICAL,
                metric_name=self.metric_name,
                message=f"{self.metric_name} exceeded critical threshold: {value:.2f}{self.unit} (target: {self.target_value:.2f}{self.unit})",
                value=value,
                threshold=self.target_value * (1 + self.critical_threshold),
            )
        elif value > self.target_value * (1 + self.warning_threshold):
            return Alert(
                level=AlertLevel.WARNING,
                metric_name=self.metric_name,
                message=f"{self.metric_name} exceeded warning threshold: {value:.2f}{self.unit} (target: {self.target_value:.2f}{self.unit})",
                value=value,
                threshold=self.target_value * (1 + self.warning_threshold),
            )
        
        return None


@dataclass
class Alert:
    """Performance alert."""
    level: AlertLevel
    metric_name: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{time_str}] {self.level.value.upper()}: {self.message}"


@dataclass
class PerformanceMeasurement:
    """Single performance measurement."""
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


class PerformanceMonitor:
    """
    Real-time performance monitoring system.
    
    Tracks performance metrics, compares against baselines,
    and generates alerts for violations.
    
    Example
    -------
    >>> monitor = PerformanceMonitor()
    >>> monitor.add_baseline('api_latency', MetricType.LATENCY, target_value=100, warning_threshold=0.5)
    >>>
    >>> # Track performance
    >>> with monitor.track('api_latency'):
    >>>     process_request()
    >>>
    >>> # Check alerts
    >>> alerts = monitor.get_recent_alerts(minutes=5)
    """
    
    def __init__(
        self,
        retention_hours: int = 24,
    ):
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.measurements: List[PerformanceMeasurement] = []
        self.alerts: List[Alert] = []
        self.retention_hours = retention_hours
        
        log.info(f"Initialized PerformanceMonitor: retention={retention_hours}h")
    
    def add_baseline(
        self,
        metric_name: str,
        metric_type: MetricType = MetricType.LATENCY,
        target_value: float = 100.0,
        warning_threshold: float = 0.5,
        critical_threshold: float = 1.0,
        unit: str = 'ms',
    ) -> None:
        """
        Add performance baseline.
        
        Parameters
        ----------
        metric_name : str
            Name of metric
        metric_type : MetricType
            Type of metric
        target_value : float
            Target value
        warning_threshold : float
            Warning threshold as percentage above target (e.g., 0.5 = 50% above)
        critical_threshold : float
            Critical threshold as percentage above target
        unit : str
            Measurement unit
        """
        self.baselines[metric_name] = PerformanceBaseline(
            metric_name=metric_name,
            metric_type=metric_type,
            target_value=target_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            unit=unit,
        )
        
        log.info(f"Added baseline: {metric_name} (target={target_value}{unit})")
    
    def track(self, metric_name: str, metadata: Optional[Dict] = None):
        """
        Context manager for tracking performance.
        
        Parameters
        ----------
        metric_name : str
            Name of metric to track
        metadata : dict, optional
            Additional metadata
        
        Example
        -------
        >>> with monitor.track('process_data'):
        >>>     process_large_dataset()
        """
        return _TrackingContext(self, metric_name, metadata or {})
    
    def record_measurement(
        self,
        metric_name: str,
        value: float,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Record a performance measurement.
        
        Parameters
        ----------
        metric_name : str
            Name of metric
        value : float
            Measured value
        metadata : dict, optional
            Additional metadata
        """
        measurement = PerformanceMeasurement(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        
        self.measurements.append(measurement)
        
        # Check against baseline
        if metric_name in self.baselines:
            alert = self.baselines[metric_name].check(value)
            if alert:
                self.alerts.append(alert)
                log.warning(f"Performance alert: {alert}")
        
        # Cleanup old measurements
        self._cleanup_old_data()
    
    def get_recent_alerts(
        self,
        minutes: Optional[int] = None,
        level: Optional[AlertLevel] = None,
    ) -> List[Alert]:
        """
        Get recent alerts.
        
        Parameters
        ----------
        minutes : int, optional
            Look back N minutes
        level : AlertLevel, optional
            Filter by alert level
        
        Returns
        -------
        list of Alert
            Recent alerts
        """
        alerts = self.alerts
        
        if minutes is not None:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            alerts = [a for a in alerts if a.timestamp >= cutoff]
        
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def get_measurements(
        self,
        metric_name: Optional[str] = None,
        minutes: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Get performance measurements as DataFrame.
        
        Parameters
        ----------
        metric_name : str, optional
            Filter by metric name
        minutes : int, optional
            Look back N minutes
        
        Returns
        -------
        pd.DataFrame
            Measurements
        """
        measurements = self.measurements
        
        if metric_name is not None:
            measurements = [m for m in measurements if m.metric_name == metric_name]
        
        if minutes is not None:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            measurements = [m for m in measurements if m.timestamp >= cutoff]
        
        if not measurements:
            return pd.DataFrame(columns=['timestamp', 'metric_name', 'value'])
        
        data = {
            'timestamp': [m.timestamp for m in measurements],
            'metric_name': [m.metric_name for m in measurements],
            'value': [m.value for m in measurements],
        }
        
        return pd.DataFrame(data)
    
    def get_statistics(
        self,
        metric_name: str,
        minutes: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Get statistics for a metric.
        
        Parameters
        ----------
        metric_name : str
            Metric name
        minutes : int, optional
            Look back N minutes
        
        Returns
        -------
        dict
            Statistics (mean, median, p95, p99, etc.)
        """
        df = self.get_measurements(metric_name=metric_name, minutes=minutes)
        
        if df.empty:
            return {}
        
        values = df['value'].values
        
        return {
            'count': len(values),
            'mean': np.mean(values),
            'median': np.median(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'p50': np.percentile(values, 50),
            'p95': np.percentile(values, 95),
            'p99': np.percentile(values, 99),
        }
    
    def check_regression(
        self,
        metric_name: str,
        lookback_minutes: int = 60,
        regression_threshold: float = 0.2,
    ) -> Optional[Alert]:
        """
        Check for performance regression.
        
        Compares recent performance to historical baseline.
        
        Parameters
        ----------
        metric_name : str
            Metric to check
        lookback_minutes : int
            Historical period for comparison
        regression_threshold : float
            Threshold for regression (percentage)
        
        Returns
        -------
        Alert, optional
            Alert if regression detected
        """
        # Get recent and historical measurements
        recent_cutoff = datetime.now() - timedelta(minutes=10)
        historical_cutoff = datetime.now() - timedelta(minutes=lookback_minutes)
        
        recent = [
            m.value for m in self.measurements
            if m.metric_name == metric_name and m.timestamp >= recent_cutoff
        ]
        
        historical = [
            m.value for m in self.measurements
            if m.metric_name == metric_name
            and historical_cutoff <= m.timestamp < recent_cutoff
        ]
        
        if not recent or not historical:
            return None
        
        recent_mean = np.mean(recent)
        historical_mean = np.mean(historical)
        
        # Check for regression
        pct_change = (recent_mean - historical_mean) / historical_mean
        
        if pct_change > regression_threshold:
            return Alert(
                level=AlertLevel.ERROR,
                metric_name=metric_name,
                message=f"Performance regression detected for {metric_name}: {pct_change:.1%} slower",
                value=recent_mean,
                threshold=historical_mean,
                metadata={
                    'recent_mean': recent_mean,
                    'historical_mean': historical_mean,
                    'pct_change': pct_change,
                },
            )
        
        return None
    
    def _cleanup_old_data(self) -> None:
        """Remove measurements older than retention period."""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        
        self.measurements = [
            m for m in self.measurements
            if m.timestamp >= cutoff
        ]
        
        self.alerts = [
            a for a in self.alerts
            if a.timestamp >= cutoff
        ]


class _TrackingContext:
    """Context manager for performance tracking."""
    
    def __init__(
        self,
        monitor: PerformanceMonitor,
        metric_name: str,
        metadata: Dict,
    ):
        self.monitor = monitor
        self.metric_name = metric_name
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
        
        self.monitor.record_measurement(
            metric_name=self.metric_name,
            value=duration,
            metadata=self.metadata,
        )
        
        return False


# Global monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    
    return _global_monitor


def reset_monitor() -> None:
    """Reset global monitor."""
    global _global_monitor
    _global_monitor = PerformanceMonitor()
