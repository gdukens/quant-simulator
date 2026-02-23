"""
Test suite for API endpoints.

Week 11: API Layer - Tests for all QuantLib Pro API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from quantlib_pro.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    return {"X-API-Key": "test_api_key_1234567890123456789012"}


# =============================================================================
# Root Endpoints Tests
# =============================================================================

def test_root_endpoint(client):
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "QuantLib Pro API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "health" in data


def test_version_endpoint(client):
    """Test version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "api_version" in data


# =============================================================================
# Health Endpoints Tests
# =============================================================================

def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_liveness_probe(client):
    """Test liveness probe."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert "alive" in data
    assert data["alive"] is True


def test_readiness_probe(client):
    """Test readiness probe."""
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "ready" in data


def test_detailed_health(client):
    """Test detailed health check."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "overall_status" in data
    assert "components" in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/health/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_snapshot(client):
    """Test metrics snapshot endpoint."""
    response = client.get("/health/metrics/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "timestamp" in data


def test_service_status(client):
    """Test service status endpoint."""
    response = client.get("/health/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "health" in data
    assert "metrics" in data


# =============================================================================
# Portfolio Endpoints Tests
# =============================================================================

def test_optimize_portfolio(client, auth_headers):
    """Test portfolio optimization endpoint."""
    payload = {
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "risk_free_rate": 0.02,
    }
    
    response = client.post("/api/v1/portfolio/optimize", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "optimal_weights" in data
    assert "expected_return" in data
    assert "volatility" in data
    assert "sharpe_ratio" in data
    
    # Verify weights sum to 1
    total_weight = sum(data["optimal_weights"].values())
    assert abs(total_weight - 1.0) < 0.01


def test_efficient_frontier(client, auth_headers):
    """Test efficient frontier endpoint."""
    payload = {
        "tickers": ["AAPL", "MSFT"],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "num_points": 20,
    }
    
    response = client.post("/api/v1/portfolio/efficient-frontier", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "returns" in data
    assert "volatilities" in data
    assert "sharpe_ratios" in data
    assert "weights" in data
    assert len(data["returns"]) == 20


# =============================================================================
# Options Endpoints Tests
# =============================================================================

def test_black_scholes_call(client, auth_headers):
    """Test Black-Scholes call option pricing."""
    payload = {
        "spot_price": 100.0,
        "strike_price": 100.0,
        "time_to_maturity": 1.0,
        "risk_free_rate": 0.05,
        "volatility": 0.2,
        "option_type": "call",
    }
    
    response = client.post("/api/v1/options/black-scholes", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "option_price" in data
    assert "delta" in data
    assert "gamma" in data
    assert "vega" in data
    assert "theta" in data
    assert "rho" in data
    assert data["option_price"] > 0


def test_black_scholes_put(client, auth_headers):
    """Test Black-Scholes put option pricing."""
    payload = {
        "spot_price": 100.0,
        "strike_price": 100.0,
        "time_to_maturity": 1.0,
        "risk_free_rate": 0.05,
        "volatility": 0.2,
        "option_type": "put",
    }
    
    response = client.post("/api/v1/options/black-scholes", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["option_price"] > 0
    # Put delta should be negative
    assert data["delta"] < 0


def test_monte_carlo_option(client, auth_headers):
    """Test Monte Carlo option pricing."""
    payload = {
        "spot_price": 100.0,
        "strike_price": 100.0,
        "time_to_maturity": 1.0,
        "risk_free_rate": 0.05,
        "volatility": 0.2,
        "option_type": "call",
        "num_simulations": 1000,
        "num_steps": 100,
        "seed": 42,
    }
    
    response = client.post("/api/v1/options/monte-carlo", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "option_price" in data
    assert "confidence_interval_95" in data
    assert "standard_error" in data
    assert len(data["confidence_interval_95"]) == 2


# =============================================================================
# Risk Endpoints Tests
# =============================================================================

def test_calculate_var(client, auth_headers):
    """Test VaR calculation."""
    # Generate sample returns
    returns = [-0.02, -0.01, 0.01, 0.02, -0.015, 0.005, -0.008] * 10
    
    payload = {
        "returns": returns,
        "confidence_level": 0.95,
        "method": "historical",
    }
    
    response = client.post("/api/v1/risk/var", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "var" in data
    assert "cvar" in data
    assert data["var"] > 0


def test_stress_test(client, auth_headers):
    """Test stress testing."""
    payload = {
        "portfolio_weights": {"AAPL": 0.5, "MSFT": 0.5},
        "tickers": ["AAPL", "MSFT"],
        "shock_magnitude": 0.5,
        "shock_type": "market_crash",
    }
    
    response = client.post("/api/v1/risk/stress-test", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "baseline_value" in data
    assert "stressed_value" in data
    assert "loss_amount" in data
    assert "loss_percentage" in data
    assert data["stressed_value"] < data["baseline_value"]


# =============================================================================
# Market Regime Endpoints Tests
# =============================================================================

def test_detect_regime(client, auth_headers):
    """Test market regime detection."""
    # Generate sample returns with clear regimes
    returns = [0.01] * 50 + [-0.02] * 50 + [0.015] * 50
    
    payload = {
        "returns": returns,
        "num_regimes": 3,
        "method": "hmm",
    }
    
    response = client.post("/api/v1/regime/detect", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "current_regime" in data
    assert "regime_probabilities" in data
    assert "regime_characteristics" in data
    assert "transitions" in data
    assert len(data["regime_probabilities"]) == 3


# =============================================================================
# Volatility Endpoints Tests
# =============================================================================

def test_implied_volatility(client, auth_headers):
    """Test implied volatility calculation."""
    payload = {
        "option_price": 10.0,
        "spot_price": 100.0,
        "strike_price": 100.0,
        "time_to_maturity": 1.0,
        "risk_free_rate": 0.05,
        "option_type": "call",
    }
    
    response = client.post("/api/v1/volatility/implied", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "implied_volatility" in data
    assert "iterations" in data
    assert "convergence_error" in data
    assert data["implied_volatility"] > 0


def test_volatility_surface(client, auth_headers):
    """Test volatility surface construction."""
    payload = {
        "ticker": "AAPL",
        "maturities": [0.25, 0.5, 1.0],
        "strikes": [90, 95, 100, 105, 110],
        "spot_price": 100.0,
    }
    
    response = client.post("/api/v1/volatility/surface", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "surface" in data
    assert "maturities" in data
    assert "strikes" in data
    assert "atm_volatilities" in data
    assert "skew" in data
    assert len(data["surface"]) == 3
    assert len(data["surface"][0]) == 5


# =============================================================================
# Macro Endpoints Tests
# =============================================================================

def test_detect_macro_regime(client, auth_headers):
    """Test macro regime detection."""
    payload = {
        "gdp_growth": [2.0, 2.5, 2.2],
        "unemployment_rate": [4.0, 3.8, 3.9],
        "pmi": [52.0, 53.0, 52.5],
    }
    
    response = client.post("/api/v1/macro/regime", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "current_regime" in data
    assert "regime_score" in data
    assert "indicators" in data
    assert "recession_probability" in data


def test_correlation_analysis(client, auth_headers):
    """Test correlation analysis."""
    payload = {
        "returns_data": {
            "AAPL": [0.01, -0.02, 0.015, -0.01] * 20,
            "MSFT": [0.012, -0.018, 0.013, -0.009] * 20,
            "GOOGL": [-0.008, 0.02, -0.012, 0.015] * 20,
        },
        "window": 30,
        "method": "pearson",
    }
    
    response = client.post("/api/v1/macro/correlation", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "correlation_matrix" in data
    assert "regime" in data
    assert "avg_correlation" in data
    assert "eigenvalue_concentration" in data
    assert "diversification_ratio" in data


def test_sentiment_analysis(client, auth_headers):
    """Test market sentiment analysis."""
    payload = {
        "vix_level": 20.0,
        "put_call_ratio": 1.1,
        "advance_decline": 100,
        "new_highs": 150,
        "new_lows": 50,
    }
    
    response = client.post("/api/v1/macro/sentiment", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "sentiment_regime" in data
    assert "fear_greed_index" in data
    assert "contrarian_signal" in data
    assert "components" in data
    assert 0 <= data["fear_greed_index"] <= 100


# =============================================================================
# Validation Tests
# =============================================================================

def test_invalid_date_range(client, auth_headers):
    """Test validation of invalid date range."""
    payload = {
        "tickers": ["AAPL"],
        "start_date": "2023-12-31",
        "end_date": "2023-01-01",  # End before start
    }
    
    response = client.post("/api/v1/portfolio/optimize", json=payload, headers=auth_headers)
    # Should fail validation (either 422 or 400)
    assert response.status_code in [400, 422]


def test_invalid_option_parameters(client, auth_headers):
    """Test validation of invalid option parameters."""
    payload = {
        "spot_price": -100.0,  # Negative price
        "strike_price": 100.0,
        "time_to_maturity": 1.0,
        "risk_free_rate": 0.05,
        "volatility": 0.2,
        "option_type": "call",
    }
    
    response = client.post("/api/v1/options/black-scholes", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_missing_required_field(client, auth_headers):
    """Test validation of missing required fields."""
    payload = {
        "spot_price": 100.0,
        # Missing strike_price and other required fields
    }
    
    response = client.post("/api/v1/options/black-scholes", json=payload, headers=auth_headers)
    assert response.status_code == 422


# =============================================================================
# Rate Limiting Tests (simplified)
# =============================================================================

def test_rate_limiting_allows_requests(client):
    """Test that rate limiting allows normal request volumes."""
    # Make a few requests - should all succeed
    for _ in range(5):
        response = client.get("/health/")
        assert response.status_code == 200


# =============================================================================
# Documentation Tests
# =============================================================================

def test_openapi_schema(client):
    """Test OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "components" in schema


def test_docs_accessible(client):
    """Test Swagger docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_accessible(client):
    """Test ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
