"""
🚀 QuantLib Pro - Production Performance Benchmarking
Validates API performance meets enterprise SLA requirements (<500ms)
"""

import time
import requests
import statistics
import threading
import concurrent.futures
from dataclasses import dataclass
from typing import List, Dict
import json
from datetime import datetime

@dataclass
class PerformanceResult:
    endpoint: str
    avg_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    success_rate: float
    total_requests: int
    
class ProductionBenchmark:
    def __init__(self, base_url: str = "http://localhost:8503"):
        self.base_url = base_url
        self.results: List[PerformanceResult] = []
        
    def test_endpoint(self, endpoint: str, num_requests: int = 100, concurrent: int = 10) -> PerformanceResult:
        """Test a single endpoint performance"""
        print(f"🧪 Testing {endpoint} ({num_requests} requests, {concurrent} concurrent)")
        
        response_times = []
        successful_requests = 0
        
        def make_request():
            nonlocal successful_requests
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    successful_requests += 1
                    return elapsed
                return None
            except Exception as e:
                print(f"❌ Request failed: {e}")
                return None
        
        # Execute requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    response_times.append(result)
        
        if not response_times:
            print(f"❌ No successful requests for {endpoint}")
            return PerformanceResult(endpoint, 0, 0, 0, 0, 0)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        success_rate = (successful_requests / num_requests) * 100
        
        result = PerformanceResult(
            endpoint=endpoint,
            avg_time_ms=avg_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            success_rate=success_rate,
            total_requests=num_requests
        )
        
        # Print results
        status_icon = "✅" if p95_time < 500 else "❌"
        print(f"{status_icon} {endpoint}:")
        print(f"   Average: {avg_time:.1f}ms")
        print(f"   95th percentile: {p95_time:.1f}ms (SLA: <500ms)")
        print(f"   99th percentile: {p99_time:.1f}ms")
        print(f"   Success rate: {success_rate:.1f}%")
        print()
        
        return result
    
    def run_full_benchmark(self) -> bool:
        """Run complete performance benchmark suite"""
        print("🚀 QuantLib Pro - Production Performance Benchmark")
        print("=" * 60)
        print(f"Target: All API endpoints <500ms (95th percentile)")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Define critical endpoints to test
        endpoints = [
            "/health",
            "/api/v1/health", 
            "/docs",
            "/api/v1/macro/regime",
            "/api/v1/macro/indicators",
            "/api/v1/portfolio/optimization/efficient-frontier",
            "/api/v1/risk/value-at-risk",
            "/api/v1/derivatives/black-scholes"
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint, num_requests=50, concurrent=10)
            self.results.append(result)
            
            # Check if meets SLA
            if result.p95_time_ms >= 500 or result.success_rate < 95:
                all_passed = False
        
        # Generate summary report
        self.generate_report()
        
        return all_passed
    
    def generate_report(self):
        """Generate detailed performance report"""
        print("📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        
        total_endpoints = len(self.results)
        passed_endpoints = sum(1 for r in self.results if r.p95_time_ms < 500 and r.success_rate >= 95)
        
        print(f"🎯 SLA Compliance: {passed_endpoints}/{total_endpoints} endpoints passed")
        print(f"📈 Overall Success Rate: {sum(r.success_rate for r in self.results) / total_endpoints:.1f}%")
        print()
        
        # Detailed results table
        print("📋 DETAILED RESULTS:")
        print("-" * 80)
        print(f"{'Endpoint':<40} {'Avg(ms)':<10} {'P95(ms)':<10} {'P99(ms)':<10} {'Success%':<10} {'Status'}")
        print("-" * 80)
        
        for result in self.results:
            status = "✅ PASS" if result.p95_time_ms < 500 and result.success_rate >= 95 else "❌ FAIL"
            print(f"{result.endpoint:<40} {result.avg_time_ms:<10.1f} {result.p95_time_ms:<10.1f} {result.p99_time_ms:<10.1f} {result.success_rate:<10.1f} {status}")
        
        print("-" * 80)
        
        # Performance recommendations
        print("\n🔧 PERFORMANCE RECOMMENDATIONS:")
        
        slow_endpoints = [r for r in self.results if r.p95_time_ms >= 400]  # Warning threshold
        if slow_endpoints:
            print("⚠️  Endpoints approaching SLA limit (≥400ms):")
            for endpoint in slow_endpoints:
                print(f"   • {endpoint.endpoint}: {endpoint.p95_time_ms:.1f}ms")
                
            print("\n💡 Optimization suggestions:")
            print("   • Enable database connection pooling")
            print("   • Implement Redis caching for heavy queries")
            print("   • Add async/await for I/O operations")
            print("   • Optimize database queries and add indexes")
        else:
            print("✅ All endpoints performing within optimal range")
        
        # Save results to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "sla_compliance": f"{passed_endpoints}/{total_endpoints}",
            "overall_success_rate": sum(r.success_rate for r in self.results) / total_endpoints,
            "results": [
                {
                    "endpoint": r.endpoint,
                    "avg_time_ms": r.avg_time_ms,
                    "p95_time_ms": r.p95_time_ms,
                    "p99_time_ms": r.p99_time_ms,
                    "success_rate": r.success_rate,
                    "total_requests": r.total_requests
                }
                for r in self.results
            ]
        }
        
        with open("performance_benchmark_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Full report saved: performance_benchmark_report.json")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="QuantLib Pro Production Performance Benchmark")
    parser.add_argument("--url", default="http://localhost:8503", help="Base URL to test")
    parser.add_argument("--endpoint", help="Test single endpoint")
    parser.add_argument("--requests", type=int, default=50, help="Number of requests per endpoint")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    
    args = parser.parse_args()
    
    benchmark = ProductionBenchmark(args.url)
    
    if args.endpoint:
        # Test single endpoint
        result = benchmark.test_endpoint(args.endpoint, args.requests, args.concurrent)
        meets_sla = result.p95_time_ms < 500 and result.success_rate >= 95
        print(f"SLA Compliance: {'✅ PASS' if meets_sla else '❌ FAIL'}")
        return 0 if meets_sla else 1
    else:
        # Run full benchmark suite
        all_passed = benchmark.run_full_benchmark()
        
        if all_passed:
            print("\n🎉 ALL PERFORMANCE BENCHMARKS PASSED!")
            print("✅ Production deployment meets enterprise SLA requirements")
            return 0
        else:
            print("\n❌ PERFORMANCE BENCHMARKS FAILED!")
            print("🔧 Optimization required before production deployment")
            return 1

if __name__ == "__main__":
    exit(main())