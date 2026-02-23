"""
Performance Profiler for QuantLib Pro.

Tools for measuring and optimizing performance:
- Function execution timing
- Memory usage tracking
- Bottleneck identification
- Performance regression detection
- Optimization recommendations

Example
-------
>>> from quantlib_pro.observability.profiler import profile, PerformanceProfiler
>>>
>>> @profile
... def expensive_calculation(n):
...     return sum(i**2 for i in range(n))
>>>
>>> profiler = PerformanceProfiler()
>>> with profiler.measure("portfolio_optimization"):
...     optimize_portfolio(...)
>>> report = profiler.generate_report()
"""

from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Try to import memory profiler
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    log.warning("psutil not available - memory profiling disabled")


T = TypeVar('T')


@dataclass
class PerformanceMeasurement:
    """Single performance measurement."""
    name: str
    start_time: float
    end_time: float
    duration: float
    memory_start: Optional[float] = None
    memory_end: Optional[float] = None
    memory_delta: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        return self.duration * 1000
    
    @property
    def memory_mb(self) -> Optional[float]:
        """Memory delta in MB."""
        if self.memory_delta is not None:
            return self.memory_delta / (1024 * 1024)
        return None


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    name: str
    count: int
    total_time: float
    min_time: float
    max_time: float
    mean_time: float
    std_time: float
    median_time: float
    p95_time: float
    p99_time: float
    
    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Count: {self.count}\n"
            f"  Total: {self.total_time*1000:.2f}ms\n"
            f"  Mean: {self.mean_time*1000:.2f}ms ± {self.std_time*1000:.2f}ms\n"
            f"  Median: {self.median_time*1000:.2f}ms\n"
            f"  Min: {self.min_time*1000:.2f}ms\n"
            f"  Max: {self.max_time*1000:.2f}ms\n"
            f"  P95: {self.p95_time*1000:.2f}ms\n"
            f"  P99: {self.p99_time*1000:.2f}ms"
        )


class PerformanceProfiler:
    """
    Performance profiler for tracking execution time and memory usage.
    
    Example
    -------
    >>> profiler = PerformanceProfiler()
    >>> with profiler.measure("calculate_var"):
    ...     var = calculate_portfolio_var(returns)
    >>> stats = profiler.get_stats("calculate_var")
    >>> print(stats)
    """
    
    def __init__(self, enable_memory_tracking: bool = True):
        self.enable_memory_tracking = enable_memory_tracking and PSUTIL_AVAILABLE
        self.measurements: Dict[str, List[PerformanceMeasurement]] = defaultdict(list)
        self._active_measurements: Dict[str, Dict] = {}
        
        if self.enable_memory_tracking:
            self.process = psutil.Process()
        else:
            self.process = None
        
        log.info("Initialized PerformanceProfiler")
    
    @contextmanager
    def measure(self, name: str, metadata: Optional[Dict] = None):
        """
        Context manager for measuring performance.
        
        Parameters
        ----------
        name : str
            Measurement name
        metadata : dict, optional
            Additional metadata
        
        Example
        -------
        >>> with profiler.measure("optimization"):
        ...     optimize_portfolio()
        """
        start_time = time.perf_counter()
        memory_start = None
        
        if self.enable_memory_tracking:
            memory_start = self.process.memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            memory_end = None
            memory_delta = None
            
            if self.enable_memory_tracking:
                memory_end = self.process.memory_info().rss
                memory_delta = memory_end - memory_start
            
            measurement = PerformanceMeasurement(
                name=name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                memory_start=memory_start,
                memory_end=memory_end,
                memory_delta=memory_delta,
                metadata=metadata or {},
            )
            
            self.measurements[name].append(measurement)
            
            log.debug(f"Measured {name}: {duration*1000:.2f}ms")
    
    def get_measurements(self, name: str) -> List[PerformanceMeasurement]:
        """Get all measurements for a specific name."""
        return self.measurements.get(name, [])
    
    def get_stats(self, name: str) -> Optional[PerformanceStats]:
        """
        Get aggregated statistics for measurements.
        
        Parameters
        ----------
        name : str
            Measurement name
        
        Returns
        -------
        PerformanceStats or None
            Aggregated statistics
        """
        measurements = self.measurements.get(name, [])
        
        if not measurements:
            return None
        
        durations = np.array([m.duration for m in measurements])
        
        return PerformanceStats(
            name=name,
            count=len(measurements),
            total_time=float(np.sum(durations)),
            min_time=float(np.min(durations)),
            max_time=float(np.max(durations)),
            mean_time=float(np.mean(durations)),
            std_time=float(np.std(durations)),
            median_time=float(np.median(durations)),
            p95_time=float(np.percentile(durations, 95)),
            p99_time=float(np.percentile(durations, 99)),
        )
    
    def generate_report(self) -> pd.DataFrame:
        """
        Generate performance report for all measurements.
        
        Returns
        -------
        pd.DataFrame
            Performance statistics table
        """
        data = []
        
        for name in sorted(self.measurements.keys()):
            stats = self.get_stats(name)
            if stats:
                data.append({
                    'Function': name,
                    'Count': stats.count,
                    'Total (ms)': f"{stats.total_time*1000:.2f}",
                    'Mean (ms)': f"{stats.mean_time*1000:.2f}",
                    'Std (ms)': f"{stats.std_time*1000:.2f}",
                    'Median (ms)': f"{stats.median_time*1000:.2f}",
                    'Min (ms)': f"{stats.min_time*1000:.2f}",
                    'Max (ms)': f"{stats.max_time*1000:.2f}",
                    'P95 (ms)': f"{stats.p95_time*1000:.2f}",
                    'P99 (ms)': f"{stats.p99_time*1000:.2f}",
                })
        
        return pd.DataFrame(data)
    
    def get_bottlenecks(self, top_n: int = 10) -> List[PerformanceStats]:
        """
        Identify performance bottlenecks.
        
        Parameters
        ----------
        top_n : int
            Number of top bottlenecks to return
        
        Returns
        -------
        list of PerformanceStats
            Top bottlenecks sorted by total time
        """
        all_stats = []
        
        for name in self.measurements.keys():
            stats = self.get_stats(name)
            if stats:
                all_stats.append(stats)
        
        # Sort by total time descending
        all_stats.sort(key=lambda s: s.total_time, reverse=True)
        
        return all_stats[:top_n]
    
    def clear(self, name: Optional[str] = None) -> None:
        """
        Clear measurements.
        
        Parameters
        ----------
        name : str, optional
            Clear specific measurement, or all if None
        """
        if name:
            if name in self.measurements:
                del self.measurements[name]
        else:
            self.measurements.clear()
    
    def export_to_csv(self, filepath: str) -> None:
        """Export report to CSV file."""
        df = self.generate_report()
        df.to_csv(filepath, index=False)
        log.info(f"Exported performance report to {filepath}")


# Global profiler instance
_global_profiler = PerformanceProfiler()


def profile(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for profiling function execution.
    
    Parameters
    ----------
    func : callable
        Function to profile
    
    Returns
    -------
    callable
        Wrapped function
    
    Example
    -------
    >>> @profile
    ... def calculate_portfolio_var(returns):
    ...     return compute_var(returns)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        
        with _global_profiler.measure(func_name):
            result = func(*args, **kwargs)
        
        return result
    
    return wrapper


def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance."""
    return _global_profiler


def print_profile_report() -> None:
    """Print performance profile report."""
    report = _global_profiler.generate_report()
    print("\nPerformance Profile Report")
    print("=" * 80)
    print(report.to_string(index=False))
    print("=" * 80)


def print_bottlenecks(top_n: int = 10) -> None:
    """Print top performance bottlenecks."""
    bottlenecks = _global_profiler.get_bottlenecks(top_n)
    
    print(f"\nTop {top_n} Performance Bottlenecks")
    print("=" * 80)
    
    for i, stats in enumerate(bottlenecks, 1):
        print(f"\n{i}. {stats}")
    
    print("=" * 80)


@dataclass
class PerformanceTarget:
    """Performance target/threshold."""
    name: str
    max_duration_ms: float
    max_memory_mb: Optional[float] = None
    
    def check(self, measurement: PerformanceMeasurement) -> bool:
        """Check if measurement meets target."""
        if measurement.duration_ms > self.max_duration_ms:
            return False
        
        if self.max_memory_mb is not None and measurement.memory_mb is not None:
            if measurement.memory_mb > self.max_memory_mb:
                return False
        
        return True


class PerformanceMonitor:
    """
    Monitor performance against targets and detect regressions.
    
    Example
    -------
    >>> monitor = PerformanceMonitor()
    >>> monitor.add_target(PerformanceTarget("var_calculation", max_duration_ms=100))
    >>> with monitor.check("var_calculation"):
    ...     calculate_var(returns)
    """
    
    def __init__(self, profiler: Optional[PerformanceProfiler] = None):
        self.profiler = profiler or _global_profiler
        self.targets: Dict[str, PerformanceTarget] = {}
        self.violations: List[Dict] = []
    
    def add_target(self, target: PerformanceTarget) -> None:
        """Add performance target."""
        self.targets[target.name] = target
        log.info(f"Added performance target: {target.name} < {target.max_duration_ms}ms")
    
    @contextmanager
    def check(self, name: str):
        """
        Context manager that checks performance against target.
        
        Parameters
        ----------
        name : str
            Target name
        """
        with self.profiler.measure(name) as _:
            yield
        
        # Check if measurement meets target
        if name in self.targets:
            measurements = self.profiler.get_measurements(name)
            if measurements:
                latest = measurements[-1]
                target = self.targets[name]
                
                if not target.check(latest):
                    violation = {
                        'timestamp': datetime.now(),
                        'name': name,
                        'duration_ms': latest.duration_ms,
                        'target_ms': target.max_duration_ms,
                        'exceeded_by_ms': latest.duration_ms - target.max_duration_ms,
                    }
                    self.violations.append(violation)
                    log.warning(
                        f"Performance target violated: {name} "
                        f"({latest.duration_ms:.2f}ms > {target.max_duration_ms}ms)"
                    )
    
    def get_violations(self) -> pd.DataFrame:
        """Get all violations as DataFrame."""
        if not self.violations:
            return pd.DataFrame()
        
        return pd.DataFrame(self.violations)
    
    def has_violations(self) -> bool:
        """Check if there are any violations."""
        return len(self.violations) > 0
