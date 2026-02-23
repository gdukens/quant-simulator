"""
UAT Performance Validation

Automated performance validation and regression detection during UAT.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import time
import statistics


class PerformanceStatus(Enum):
    """Performance test status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class PerformanceBenchmark:
    """Performance benchmark definition."""
    name: str
    description: str
    test_function: Callable
    baseline_ms: float  # Expected baseline in milliseconds
    threshold_ms: float  # Failure threshold
    warning_ms: float  # Warning threshold
    category: str = "general"
    
    def __post_init__(self):
        """Validate thresholds."""
        if self.warning_ms < self.baseline_ms:
            self.warning_ms = self.baseline_ms * 1.2
        if self.threshold_ms < self.warning_ms:
            self.threshold_ms = self.warning_ms * 1.5


@dataclass
class PerformanceResult:
    """Performance test result."""
    benchmark_name: str
    timestamp: datetime
    executions: int
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    status: PerformanceStatus
    baseline_ms: float
    threshold_ms: float
    regression_pct: float = 0.0  # % slower than baseline
    notes: str = ""
    
    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == PerformanceStatus.PASS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'benchmark_name': self.benchmark_name,
            'timestamp': self.timestamp.isoformat(),
            'executions': self.executions,
            'mean_ms': round(self.mean_ms, 2),
            'median_ms': round(self.median_ms, 2),
            'p95_ms': round(self.p95_ms, 2),
            'p99_ms': round(self.p99_ms, 2),
            'min_ms': round(self.min_ms, 2),
            'max_ms': round(self.max_ms, 2),
            'std_dev_ms': round(self.std_dev_ms, 2),
            'status': self.status.value,
            'baseline_ms': self.baseline_ms,
            'threshold_ms': self.threshold_ms,
            'regression_pct': round(self.regression_pct, 2),
            'passed': self.passed,
            'notes': self.notes,
        }


class PerformanceValidator:
    """Validate performance during UAT."""
    
    def __init__(self):
        """Initialize validator."""
        self.benchmarks: List[PerformanceBenchmark] = []
        self.results: List[PerformanceResult] = []
        self._register_default_benchmarks()
    
    def _register_default_benchmarks(self) -> None:
        """Register default performance benchmarks."""
        # These would be implemented with actual test functions
        
        # Portfolio optimization benchmarks
        self.register_benchmark(PerformanceBenchmark(
            name="portfolio_optimization_10_stocks",
            description="Optimize portfolio with 10 stocks, 1 year data",
            test_function=lambda: self._mock_test(0.3),  # Placeholder
            baseline_ms=300.0,
            threshold_ms=600.0,
            warning_ms=400.0,
            category="portfolio"
        ))
        
        self.register_benchmark(PerformanceBenchmark(
            name="portfolio_optimization_50_stocks",
            description="Optimize portfolio with 50 stocks, 1 year data",
            test_function=lambda: self._mock_test(1.2),
            baseline_ms=1200.0,
            threshold_ms=2500.0,
            warning_ms=1800.0,
            category="portfolio"
        ))
        
        self.register_benchmark(PerformanceBenchmark(
            name="efficient_frontier_50_points",
            description="Generate 50-point efficient frontier",
            test_function=lambda: self._mock_test(2.0),
            baseline_ms=2000.0,
            threshold_ms=4000.0,
            warning_ms=3000.0,
            category="portfolio"
        ))
        
        # Risk calculation benchmarks
        self.register_benchmark(PerformanceBenchmark(
            name="var_parametric",
            description="Calculate parametric VaR",
            test_function=lambda: self._mock_test(0.05),
            baseline_ms=50.0,
            threshold_ms=100.0,
            warning_ms=75.0,
            category="risk"
        ))
        
        self.register_benchmark(PerformanceBenchmark(
            name="var_historical",
            description="Calculate historical VaR (3 years data)",
            test_function=lambda: self._mock_test(0.08),
            baseline_ms=80.0,
            threshold_ms=150.0,
            warning_ms=120.0,
            category="risk"
        ))
        
        self.register_benchmark(PerformanceBenchmark(
            name="var_monte_carlo_10k",
            description="Monte Carlo VaR with 10K simulations",
            test_function=lambda: self._mock_test(0.5),
            baseline_ms=500.0,
            threshold_ms=1000.0,
            warning_ms=750.0,
            category="risk"
        ))
        
        # Options pricing benchmarks
        self.register_benchmark(PerformanceBenchmark(
            name="black_scholes_single",
            description="Price single option with Black-Scholes",
            test_function=lambda: self._mock_test(0.02),
            baseline_ms=20.0,
            threshold_ms=50.0,
            warning_ms=35.0,
            category="options"
        ))
        
        self.register_benchmark(PerformanceBenchmark(
            name="black_scholes_greeks",
            description="Calculate all Greeks for option",
            test_function=lambda: self._mock_test(0.04),
            baseline_ms=40.0,
            threshold_ms=80.0,
            warning_ms=60.0,
            category="options"
        ))
        
        self.register_benchmark(PerformanceBenchmark(
            name="monte_carlo_option_100k",
            description="Price option with 100K Monte Carlo paths",
            test_function=lambda: self._mock_test(1.5),
            baseline_ms=1500.0,
            threshold_ms=3000.0,
            warning_ms=2200.0,
            category="options"
        ))
        
        # Regime detection benchmarks
        self.register_benchmark(PerformanceBenchmark(
            name="hmm_regime_detection_3yr",
            description="HMM regime detection on 3 years data",
            test_function=lambda: self._mock_test(0.15),
            baseline_ms=150.0,
            threshold_ms=300.0,
            warning_ms=225.0,
            category="regime"
        ))
        
        # Backtesting benchmarks
        self.register_benchmark(PerformanceBenchmark(
            name="backtest_simple_strategy_3yr",
            description="Backtest simple strategy on 3 years data",
            test_function=lambda: self._mock_test(0.25),
            baseline_ms=250.0,
            threshold_ms=500.0,
            warning_ms=375.0,
            category="backtest"
        ))
    
    def _mock_test(self, duration_seconds: float) -> None:
        """Mock test function that sleeps."""
        time.sleep(duration_seconds)
    
    def register_benchmark(self, benchmark: PerformanceBenchmark) -> None:
        """Register a performance benchmark."""
        self.benchmarks.append(benchmark)
    
    def run_benchmark(
        self,
        benchmark: PerformanceBenchmark,
        executions: int = 10
    ) -> PerformanceResult:
        """
        Run a single benchmark.
        
        Args:
            benchmark: Benchmark to run
            executions: Number of executions
            
        Returns:
            Performance result
        """
        times_ms = []
        
        for _ in range(executions):
            start = time.perf_counter()
            try:
                benchmark.test_function()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                times_ms.append(elapsed_ms)
            except Exception as e:
                # Record failure
                return PerformanceResult(
                    benchmark_name=benchmark.name,
                    timestamp=datetime.now(),
                    executions=0,
                    mean_ms=0,
                    median_ms=0,
                    p95_ms=0,
                    p99_ms=0,
                    min_ms=0,
                    max_ms=0,
                    std_dev_ms=0,
                    status=PerformanceStatus.FAIL,
                    baseline_ms=benchmark.baseline_ms,
                    threshold_ms=benchmark.threshold_ms,
                    notes=f"Execution error: {str(e)}"
                )
        
        # Calculate statistics
        mean_ms = statistics.mean(times_ms)
        median_ms = statistics.median(times_ms)
        std_dev_ms = statistics.stdev(times_ms) if len(times_ms) > 1 else 0
        
        sorted_times = sorted(times_ms)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        p95_ms = sorted_times[p95_index]
        p99_ms = sorted_times[p99_index]
        
        # Determine status
        regression_pct = ((mean_ms - benchmark.baseline_ms) / benchmark.baseline_ms) * 100
        
        if mean_ms > benchmark.threshold_ms:
            status = PerformanceStatus.FAIL
        elif mean_ms > benchmark.warning_ms:
            status = PerformanceStatus.WARNING
        else:
            status = PerformanceStatus.PASS
        
        result = PerformanceResult(
            benchmark_name=benchmark.name,
            timestamp=datetime.now(),
            executions=executions,
            mean_ms=mean_ms,
            median_ms=median_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
            min_ms=min(times_ms),
            max_ms=max(times_ms),
            std_dev_ms=std_dev_ms,
            status=status,
            baseline_ms=benchmark.baseline_ms,
            threshold_ms=benchmark.threshold_ms,
            regression_pct=regression_pct
        )
        
        self.results.append(result)
        return result
    
    def run_all_benchmarks(
        self,
        category: Optional[str] = None,
        executions: int = 10
    ) -> List[PerformanceResult]:
        """
        Run all benchmarks.
        
        Args:
            category: Filter by category
            executions: Number of executions per benchmark
            
        Returns:
            List of results
        """
        benchmarks = self.benchmarks
        if category:
            benchmarks = [b for b in benchmarks if b.category == category]
        
        results = []
        for benchmark in benchmarks:
            result = self.run_benchmark(benchmark, executions)
            results.append(result)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get performance validation summary.
        
        Returns:
            Summary statistics
        """
        if not self.results:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
            }
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == PerformanceStatus.PASS)
        failed = sum(1 for r in self.results if r.status == PerformanceStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == PerformanceStatus.WARNING)
        
        # By category
        categories = set(b.category for b in self.benchmarks)
        by_category = {}
        for category in categories:
            cat_results = [
                r for r in self.results
                if any(b.name == r.benchmark_name and b.category == category for b in self.benchmarks)
            ]
            if cat_results:
                by_category[category] = {
                    'total': len(cat_results),
                    'passed': sum(1 for r in cat_results if r.status == PerformanceStatus.PASS),
                    'failed': sum(1 for r in cat_results if r.status == PerformanceStatus.FAIL),
                    'warnings': sum(1 for r in cat_results if r.status == PerformanceStatus.WARNING),
                }
        
        # Regressions
        regressions = [r for r in self.results if r.regression_pct > 10.0]
        worst_regression = max(self.results, key=lambda r: r.regression_pct) if self.results else None
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'by_category': by_category,
            'regressions_count': len(regressions),
            'worst_regression': worst_regression.to_dict() if worst_regression else None,
        }
    
    def get_failing_benchmarks(self) -> List[PerformanceResult]:
        """Get all failing benchmarks."""
        return [r for r in self.results if r.status == PerformanceStatus.FAIL]
    
    def get_regressions(self, threshold_pct: float = 10.0) -> List[PerformanceResult]:
        """
        Get performance regressions.
        
        Args:
            threshold_pct: Regression threshold percentage
            
        Returns:
            List of regressed results
        """
        return [r for r in self.results if r.regression_pct > threshold_pct]
    
    def compare_with_baseline(self, baseline_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare current results with baseline.
        
        Args:
            baseline_results: Previous baseline results
            
        Returns:
            Comparison report
        """
        baseline_map = {r['benchmark_name']: r for r in baseline_results}
        
        comparisons = []
        for result in self.results:
            if result.benchmark_name in baseline_map:
                baseline = baseline_map[result.benchmark_name]
                baseline_mean = baseline['mean_ms']
                current_mean = result.mean_ms
                delta_pct = ((current_mean - baseline_mean) / baseline_mean) * 100
                
                comparisons.append({
                    'benchmark_name': result.benchmark_name,
                    'baseline_mean_ms': baseline_mean,
                    'current_mean_ms': current_mean,
                    'delta_ms': current_mean - baseline_mean,
                    'delta_pct': delta_pct,
                    'improved': delta_pct < 0,
                    'regressed': delta_pct > 10.0,
                })
        
        improved = [c for c in comparisons if c['improved']]
        regressed = [c for c in comparisons if c['regressed']]
        
        return {
            'comparisons': comparisons,
            'improved_count': len(improved),
            'regressed_count': len(regressed),
            'stable_count': len(comparisons) - len(improved) - len(regressed),
            'improvements': sorted(improved, key=lambda x: x['delta_pct']),
            'regressions': sorted(regressed, key=lambda x: x['delta_pct'], reverse=True),
        }
    
    def export_report(self, filepath: str) -> None:
        """Export performance validation report."""
        import json
        
        report = {
            'summary': self.get_summary(),
            'results': [r.to_dict() for r in self.results],
            'failures': [r.to_dict() for r in self.get_failing_benchmarks()],
            'regressions': [r.to_dict() for r in self.get_regressions()],
            'generated_at': datetime.now().isoformat(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
