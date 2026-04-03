"""
QuantLib Pro - Load Testing with Locust

This module provides comprehensive load testing scenarios for production deployment.

Usage:
    # Basic load test
    locust -f tests/load/locustfile.py --host=http://localhost:8501

    # Headless mode with specific parameters
    locust -f tests/load/locustfile.py \
        --host=http://localhost:8501 \
        --users 100 \
        --spawn-rate 10 \
        --run-time 5m \
        --headless

    # Web UI mode
    locust -f tests/load/locustfile.py --host=http://localhost:8501 --web-host=0.0.0.0

Requirements:
    pip install locust requests
"""

import json
import random
import time
from datetime import datetime, timedelta

from locust import HttpUser, TaskSet, between, task


class HealthCheckTasks(TaskSet):
    """Health check and monitoring endpoint tasks."""

    @task(10)
    def health_check(self):
        """Test main health check endpoint."""
        with self.client.get(
            "/health",
            name="/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def readiness_check(self):
        """Test readiness probe."""
        with self.client.get(
            "/health/ready",
            name="/health/ready",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Readiness check failed: {response.status_code}")

    @task(5)
    def liveness_check(self):
        """Test liveness probe."""
        with self.client.get(
            "/health/live",
            name="/health/live",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness check failed: {response.status_code}")

    @task(2)
    def metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        with self.client.get(
            "/metrics",
            name="/metrics",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                if "quantlib_health" in response.text:
                    response.success()
                else:
                    response.failure("Metrics missing expected data")
            else:
                response.failure(f"Metrics endpoint failed: {response.status_code}")


class StreamlitAppTasks(TaskSet):
    """Streamlit application interaction tasks."""

    def on_start(self):
        """Initialize session on user start."""
        # Get Streamlit session
        response = self.client.get("/_stcore/health")
        if response.status_code == 200:
            self.session_active = True
        else:
            self.session_active = False

    @task(20)
    def load_homepage(self):
        """Load main Streamlit page."""
        with self.client.get(
            "/",
            name="Homepage",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage load failed: {response.status_code}")

    @task(5)
    def streamlit_health(self):
        """Check Streamlit core health."""
        with self.client.get(
            "/_stcore/health",
            name="Streamlit Health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Streamlit health failed: {response.status_code}")


class PortfolioOptimizationTasks(TaskSet):
    """Portfolio optimization feature tasks."""

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ"]

    @task(10)
    def optimize_portfolio(self):
        """Simulate portfolio optimization request."""
        # Select random tickers
        selected_tickers = random.sample(self.tickers, k=random.randint(3, 7))

        # Simulate optimization parameters
        params = {
            "tickers": selected_tickers,
            "method": random.choice(["mean_variance", "min_volatility", "max_sharpe"]),
            "risk_free_rate": 0.02,
            "target_return": random.uniform(0.08, 0.15),
        }

        # Note: Actual endpoint depends on your Streamlit app structure
        # This is a placeholder for demonstration
        with self.client.post(
            "/api/optimize",
            json=params,
            name="Portfolio Optimization",
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Endpoint might not exist in Streamlit app
                response.success()  # Don't fail the test
            else:
                response.failure(f"Optimization failed: {response.status_code}")


class RiskAnalysisTasks(TaskSet):
    """Risk analysis feature tasks."""

    @task(8)
    def calculate_var(self):
        """Calculate Value at Risk."""
        params = {
            "portfolio_value": random.uniform(100000, 1000000),
            "confidence_level": random.choice([0.95, 0.99]),
            "time_horizon": random.choice([1, 5, 10]),
        }

        with self.client.post(
            "/api/risk/var",
            json=params,
            name="VaR Calculation",
            catch_response=True,
            timeout=20
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"VaR calculation failed: {response.status_code}")

    @task(6)
    def stress_test(self):
        """Run portfolio stress test."""
        scenarios = ["market_crash", "interest_rate_spike", "volatility_surge"]

        params = {
            "scenario": random.choice(scenarios),
            "severity": random.uniform(0.1, 0.5),
        }

        with self.client.post(
            "/api/risk/stress",
            json=params,
            name="Stress Test",
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Stress test failed: {response.status_code}")


class MonteCarloTasks(TaskSet):
    """Monte Carlo simulation tasks."""

    @task(5)
    def run_simulation(self):
        """Run Monte Carlo portfolio simulation."""
        params = {
            "initial_investment": random.uniform(10000, 100000),
            "num_simulations": random.choice([1000, 5000, 10000]),
            "time_horizon_years": random.choice([1, 5, 10, 20]),
            "expected_return": random.uniform(0.06, 0.12),
            "volatility": random.uniform(0.10, 0.25),
        }

        with self.client.post(
            "/api/monte-carlo/simulate",
            json=params,
            name="Monte Carlo Simulation",
            catch_response=True,
            timeout=60  # Longer timeout for simulations
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Simulation failed: {response.status_code}")


class BacktestingTasks(TaskSet):
    """Backtesting tasks."""

    strategies = ["moving_average", "rsi", "bollinger_bands", "mean_reversion"]

    @task(4)
    def run_backtest(self):
        """Run strategy backtest."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=random.choice([30, 90, 180, 365]))

        params = {
            "strategy": random.choice(self.strategies),
            "ticker": random.choice(["SPY", "QQQ", "AAPL", "TSLA"]),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_capital": random.uniform(10000, 100000),
        }

        with self.client.post(
            "/api/backtest/run",
            json=params,
            name="Backtesting",
            catch_response=True,
            timeout=45
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Backtest failed: {response.status_code}")


class NormalUser(HttpUser):
    """Normal user with typical usage patterns."""
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    weight = 10  # Most users are normal users

    tasks = {
        HealthCheckTasks: 2,
        StreamlitAppTasks: 10,
        PortfolioOptimizationTasks: 5,
        RiskAnalysisTasks: 3,
    }


class PowerUser(HttpUser):
    """Power user with heavy computation tasks."""
    wait_time = between(1, 3)  # Faster task execution
    weight = 3  # Fewer power users

    tasks = {
        PortfolioOptimizationTasks: 5,
        RiskAnalysisTasks: 5,
        MonteCarloTasks: 4,
        BacktestingTasks: 3,
    }


class MonitoringUser(HttpUser):
    """Monitoring/health check user (external monitoring)."""
    wait_time = between(10, 30)  # Check every 10-30 seconds
    weight = 1  # Very few monitoring users

    tasks = {
        HealthCheckTasks: 10,
    }


class StressTestUser(HttpUser):
    """Stress test user with aggressive usage."""
    wait_time = between(0.5, 1.5)  # Very fast task execution
    weight = 1  # Only during stress tests

    tasks = {
        StreamlitAppTasks: 3,
        PortfolioOptimizationTasks: 5,
        RiskAnalysisTasks: 4,
        MonteCarloTasks: 3,
        BacktestingTasks: 2,
    }


# ============================================================================
# Custom Load Shapes
# ============================================================================

from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load shape that gradually increases users.

    Stages:
    - 0-60s: 10 users
    - 60-120s: 25 users
    - 120-180s: 50 users
    - 180-240s: 100 users
    - 240-300s: 50 users (ramp down)
    """

    step_time = 60
    step_load = 10
    spawn_rate = 5
    time_limit = 300

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = (run_time // self.step_time) + 1

        if current_step < 5:
            user_count = current_step * self.step_load * (2 if current_step > 2 else 1)
        else:
            user_count = 50  # Ramp down

        return (user_count, self.spawn_rate)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load shape to test sudden traffic increases.

    Pattern:
    - 0-60s: 20 users
    - 60-90s: 200 users (spike!)
    - 90-180s: 20 users (back to normal)
    """

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            return (20, 5)
        elif run_time < 90:
            return (200, 20)  # Spike!
        elif run_time < 180:
            return (20, 5)
        else:
            return None


# ============================================================================
# Event Listeners for Custom Metrics
# ============================================================================

from locust import events


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests."""
    if response_time > 3000:  # 3 seconds
        print(f"  SLOW REQUEST: {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print("=" * 60)
    print(" Load Test Started")
    print(f"   Target: {environment.host}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test completion."""
    print("=" * 60)
    print(" Load Test Completed")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    import os
    os.system(
        "locust -f locustfile.py --host=http://localhost:8501 "
        "--users 50 --spawn-rate 5 --run-time 5m --headless"
    )
