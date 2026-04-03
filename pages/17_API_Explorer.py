"""
QuantLib Pro - API Explorer Dashboard
======================================
A Postman-style API testing interface with:
- Global search with fuzzy matching
- Endpoint collections browser
- Request builder with params/headers/body
- Response viewer (JSON/Table/Chart)
- Code playground with live execution
- Responsive layout
"""

import io
import json
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Note: page config is set globally in streamlit_app.py

# ==============================================================================
# CUSTOM CSS - Clean, Professional, No Emojis
# ==============================================================================
st.markdown("""
<style>
/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Main container */
.main .block-container {
    padding: 1rem 2rem;
    max-width: 100%;
}

/* Header bar */
.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 8px;
    margin-bottom: 16px;
    border: 1px solid #2d3748;
}
.header-title {
    font-size: 24px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.5px;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.status-online {
    background: rgba(72, 187, 120, 0.15);
    color: #48bb78;
    border: 1px solid rgba(72, 187, 120, 0.3);
}
.status-offline {
    background: rgba(245, 101, 101, 0.15);
    color: #f56565;
    border: 1px solid rgba(245, 101, 101, 0.3);
}
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
}

/* Search bar */
.search-container {
    margin-bottom: 16px;
}

/* URL bar */
.url-bar-container {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #1e1e2e;
    border: 1px solid #3d3d5c;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 16px;
}
.method-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 12px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    text-transform: uppercase;
    min-width: 60px;
    text-align: center;
}
.method-get { background: #61affe; color: #fff; }
.method-post { background: #49cc90; color: #fff; }
.method-put { background: #fca130; color: #1a1a2e; }
.method-delete { background: #f93e3e; color: #fff; }
.method-patch { background: #50e3c2; color: #1a1a2e; }

/* Panels */
.panel {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    overflow: hidden;
}
.panel-header {
    background: #161b22;
    padding: 10px 16px;
    border-bottom: 1px solid #30363d;
    font-weight: 600;
    font-size: 13px;
    color: #c9d1d9;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.panel-body {
    padding: 12px;
}

/* Endpoint list */
.endpoint-category {
    margin-bottom: 8px;
}
.category-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #161b22;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    font-size: 13px;
    color: #8b949e;
    transition: background 0.2s;
}
.category-header:hover {
    background: #1f2937;
}
.category-count {
    background: #30363d;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
}
.endpoint-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px 8px 24px;
    cursor: pointer;
    border-radius: 4px;
    transition: background 0.15s;
    font-size: 13px;
    color: #c9d1d9;
}
.endpoint-item:hover {
    background: #1f2937;
}
.endpoint-item.active {
    background: #238636;
    color: #fff;
}
.method-tag {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: monospace;
}
.method-tag-get { background: #61affe22; color: #61affe; }
.method-tag-post { background: #49cc9022; color: #49cc90; }
.method-tag-put { background: #fca13022; color: #fca130; }
.method-tag-delete { background: #f93e3e22; color: #f93e3e; }

/* Response status */
.response-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 13px;
}
.status-2xx { background: #49cc9022; color: #49cc90; }
.status-4xx { background: #fca13022; color: #fca130; }
.status-5xx { background: #f93e3e22; color: #f93e3e; }
.status-err { background: #f93e3e22; color: #f93e3e; }

/* Code editor area */
.code-editor {
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
}

/* Tabs override */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #161b22;
    padding: 4px;
    border-radius: 6px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #30363d;
}

/* Button styles */
.btn-primary {
    background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
    color: white;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.1s, box-shadow 0.2s;
}
.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(35, 134, 54, 0.3);
}

/* Responsive */
@media (max-width: 1024px) {
    .main .block-container {
        padding: 0.5rem 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# API CONFIGURATION
# ==============================================================================
API_BASE = "http://localhost:8001"

# ==============================================================================
# ENDPOINT CATALOG
# ==============================================================================
ENDPOINTS = {
    "Health": {
        "endpoints": [
            {"name": "Health Check", "method": "GET", "path": "/health", "description": "Check API health status", "params": [], "body": None},
            {"name": "Root Info", "method": "GET", "path": "/", "description": "Get API information", "params": [], "body": None},
        ]
    },
    "Real-Time Data": {
        "endpoints": [
            {"name": "Get Quote", "method": "GET", "path": "/api/v1/realdata/quote/{symbol}", "description": "Get real-time stock quote",
             "params": [{"name": "symbol", "type": "path", "default": "AAPL", "description": "Stock symbol"}], "body": None},
            {"name": "Batch Quotes", "method": "POST", "path": "/api/v1/realdata/quote/batch", "description": "Get multiple quotes",
             "params": [], "body": {"symbols": ["AAPL", "GOOGL", "MSFT"]}},
            {"name": "Historical Data", "method": "POST", "path": "/api/v1/realdata/historical", "description": "Get historical OHLCV",
             "params": [], "body": {"symbol": "AAPL", "period": "1mo", "interval": "1d"}},
            {"name": "Data Health", "method": "GET", "path": "/api/v1/realdata/health", "description": "Check data providers",
             "params": [], "body": None},
        ]
    },
    "Portfolio": {
        "endpoints": [
            {"name": "Optimize Portfolio", "method": "POST", "path": "/api/v1/portfolio/optimize", "description": "Optimize weights using MPT",
             "params": [], "body": {"tickers": ["AAPL", "GOOGL", "MSFT", "AMZN"], "budget": 100000, "risk_free_rate": 0.045, "optimization_target": "sharpe", "max_position_size": 0.4}},
            {"name": "Efficient Frontier", "method": "POST", "path": "/api/v1/portfolio/efficient-frontier", "description": "Generate frontier curve",
             "params": [], "body": {"tickers": ["AAPL", "GOOGL", "MSFT"], "n_portfolios": 500}},
            {"name": "Portfolio Performance", "method": "GET", "path": "/api/v1/portfolio/performance", "description": "Get performance metrics",
             "params": [{"name": "portfolio_id", "type": "query", "default": "demo", "description": "Portfolio ID"}], "body": None},
        ]
    },
    "Risk Analysis": {
        "endpoints": [
            {"name": "Value at Risk", "method": "POST", "path": "/api/v1/risk/var", "description": "Calculate VaR and CVaR",
             "params": [], "body": {"portfolio_id": "demo", "confidence_level": 0.95, "method": "historical", "horizon_days": 10}},
            {"name": "Stress Test", "method": "POST", "path": "/api/v1/risk/stress-test", "description": "Run stress scenarios",
             "params": [], "body": {"portfolio_id": "demo", "scenarios": ["2008_crisis", "covid_crash"]}},
            {"name": "Greeks Calculator", "method": "POST", "path": "/api/v1/risk/greeks", "description": "Calculate option Greeks",
             "params": [], "body": {"spot": 100, "strike": 100, "rate": 0.05, "volatility": 0.2, "expiry_days": 30, "option_type": "call"}},
        ]
    },
    "Options": {
        "endpoints": [
            {"name": "Black-Scholes Price", "method": "POST", "path": "/api/v1/options/price", "description": "Price using Black-Scholes",
             "params": [], "body": {"spot": 100, "strike": 100, "rate": 0.05, "volatility": 0.2, "expiry_days": 30, "option_type": "call"}},
            {"name": "Implied Volatility", "method": "POST", "path": "/api/v1/options/implied-volatility", "description": "Calculate IV from price",
             "params": [], "body": {"spot": 100, "strike": 100, "rate": 0.05, "expiry_days": 30, "option_price": 5.5, "option_type": "call"}},
            {"name": "Monte Carlo Price", "method": "POST", "path": "/api/v1/options/monte-carlo", "description": "Monte Carlo pricing",
             "params": [], "body": {"spot": 100, "strike": 100, "rate": 0.05, "volatility": 0.2, "expiry_days": 30, "n_simulations": 10000, "option_type": "call"}},
        ]
    },
    "Market Regime": {
        "endpoints": [
            {"name": "Detect Regime", "method": "POST", "path": "/api/v1/regime/detect", "description": "Detect market regime using HMM",
             "params": [], "body": {"ticker": "SPY", "lookback_days": 252, "n_regimes": 3}},
            {"name": "Regime Probability", "method": "GET", "path": "/api/v1/regime/probability/{ticker}", "description": "Get regime probabilities",
             "params": [{"name": "ticker", "type": "path", "default": "SPY", "description": "Ticker symbol"}], "body": None},
        ]
    },
    "Volatility": {
        "endpoints": [
            {"name": "Volatility Surface", "method": "POST", "path": "/api/v1/volatility/surface", "description": "Generate vol surface",
             "params": [], "body": {"ticker": "SPY", "strikes": [90, 95, 100, 105, 110], "expiries": [7, 14, 30, 60, 90]}},
            {"name": "GARCH Forecast", "method": "POST", "path": "/api/v1/volatility/garch", "description": "Forecast with GARCH",
             "params": [], "body": {"ticker": "SPY", "forecast_days": 10}},
        ]
    },
    "Macro": {
        "endpoints": [
            {"name": "Economic Indicators", "method": "GET", "path": "/api/v1/macro/indicators", "description": "Get economic indicators",
             "params": [{"name": "country", "type": "query", "default": "US", "description": "Country code"}], "body": None},
            {"name": "Yield Curve", "method": "GET", "path": "/api/v1/macro/yield-curve", "description": "Get yield curve",
             "params": [], "body": None},
        ]
    },
    "Backtesting": {
        "endpoints": [
            {"name": "Run Backtest", "method": "POST", "path": "/api/v1/backtest/run", "description": "Run strategy backtest",
             "params": [], "body": {"strategy": "momentum", "tickers": ["AAPL", "GOOGL"], "start_date": "2023-01-01", "end_date": "2024-01-01", "initial_capital": 100000}},
            {"name": "Backtest Results", "method": "GET", "path": "/api/v1/backtest/results/{backtest_id}", "description": "Get results",
             "params": [{"name": "backtest_id", "type": "path", "default": "bt_001", "description": "Backtest ID"}], "body": None},
        ]
    },
    "Execution": {
        "endpoints": [
            {"name": "Market Impact", "method": "POST", "path": "/api/v1/execution/market-impact", "description": "Estimate market impact",
             "params": [], "body": {"ticker": "AAPL", "quantity": 10000, "side": "buy"}},
            {"name": "Optimal Execution", "method": "POST", "path": "/api/v1/execution/optimal", "description": "Calculate optimal execution",
             "params": [], "body": {"ticker": "AAPL", "quantity": 50000, "urgency": "medium", "algorithm": "twap"}},
        ]
    },
}


# ==============================================================================
# SESSION STATE
# ==============================================================================
if "selected_endpoint" not in st.session_state:
    st.session_state.selected_endpoint = None
if "request_history" not in st.session_state:
    st.session_state.request_history = []
if "response_data" not in st.session_state:
    st.session_state.response_data = None
if "response_status" not in st.session_state:
    st.session_state.response_status = None
if "response_time" not in st.session_state:
    st.session_state.response_time = None
if "code_output" not in st.session_state:
    st.session_state.code_output = None
if "expanded_categories" not in st.session_state:
    st.session_state.expanded_categories = set()


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def check_api_status() -> bool:
    """Check if API server is online."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=2)
        return resp.status_code == 200
    except:
        return False


def execute_request(method: str, url: str, params: dict = None, body: dict = None) -> tuple:
    """Execute HTTP request with comprehensive error handling."""
    start = time.time()
    try:
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=body, params=params, headers=headers, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=body, params=params, headers=headers, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, params=params, headers=headers, timeout=30)
        else:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        
        elapsed = (time.time() - start) * 1000
        
        # Try to parse JSON response
        try:
            data = resp.json()
        except json.JSONDecodeError:
            # If not JSON, return text response
            if resp.text:
                data = {"raw_response": resp.text, "content_type": resp.headers.get("content-type", "unknown")}
            else:
                data = {"message": "Empty response", "status": "success" if 200 <= resp.status_code < 300 else "error"}
        
        return resp.status_code, data, elapsed
    
    except requests.exceptions.ConnectionError:
        elapsed = (time.time() - start) * 1000
        return 0, {
            "error": "Connection Error",
            "message": "Could not connect to API server. Is it running on the correct port?",
            "url": url,
            "suggestion": "Check that uvicorn is running: uvicorn main_api:app --port 8001"
        }, elapsed
    
    except requests.exceptions.Timeout:
        return 0, {
            "error": "Timeout Error",
            "message": "Request took longer than 30 seconds",
            "suggestion": "The endpoint may be processing a heavy computation. Try with smaller parameters."
        }, 30000
    
    except requests.exceptions.RequestException as e:
        elapsed = (time.time() - start) * 1000
        return 0, {
            "error": "Request Error",
            "message": str(e),
            "type": type(e).__name__
        }, elapsed
    
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return 0, {
            "error": "Unknown Error",
            "message": str(e),
            "type": type(e).__name__
        }, elapsed


def build_url(path: str, path_params: dict) -> str:
    """Build URL with path parameters."""
    url = path
    for k, v in path_params.items():
        url = url.replace(f"{{{k}}}", str(v))
    return API_BASE + url


def generate_python_code(method: str, url: str, params: dict = None, body: dict = None) -> str:
    """Generate Python code with clearly marked editable parameters."""
    lines = [
        "# ===== API REQUEST TEMPLATE =====",
        "# Edit the parameters below as needed",
        "import requests",
        "import json",
        ""
    ]
    
    # Add URL as a variable for easy editing
    lines.extend([
        "# ===== ENDPOINT URL (Edit if needed) =====",
        f'API_URL = "{url}"',
        ""
    ])
    
    # Add query parameters section if present
    if params:
        lines.extend([
            "# ===== QUERY PARAMETERS (Edit values below) =====",
            f"params = {json.dumps(params, indent=4)}",
            ""
        ])
    
    # Add request body section if present
    if body:
        lines.extend([
            "# ===== REQUEST BODY (Edit fields below) =====",
            f"payload = {json.dumps(body, indent=4)}",
            ""
        ])
    
    # Add execution section
    lines.append("# ===== EXECUTE REQUEST =====")
    if method == "GET":
        if params:
            lines.append('response = requests.get(API_URL, params=params, timeout=30)')
        else:
            lines.append('response = requests.get(API_URL, timeout=30)')
    else:
        if body and params:
            lines.append(f'response = requests.{method.lower()}(API_URL, json=payload, params=params, timeout=30)')
        elif body:
            lines.append(f'response = requests.{method.lower()}(API_URL, json=payload, timeout=30)')
        elif params:
            lines.append(f'response = requests.{method.lower()}(API_URL, params=params, timeout=30)')
        else:
            lines.append(f'response = requests.{method.lower()}(API_URL, timeout=30)')
    
    # Add response handling
    lines.extend([
        "",
        "# ===== HANDLE RESPONSE =====",
        "if response.status_code == 200:",
        "    print(' Success!')",
        "    data = response.json()",
        "    print(json.dumps(data, indent=2))",
        "else:",
        "    print(f' Error: {response.status_code}')",
        "    print(response.text)"
    ])
    
    return "\n".join(lines)


def generate_curl_code(method: str, url: str, params: dict = None, body: dict = None) -> str:
    """Generate curl command."""
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"
    else:
        full_url = url
    
    if method == "GET":
        return f'curl -X GET "{full_url}"'
    else:
        if body:
            body_str = json.dumps(body)
            return f'curl -X {method} "{full_url}" \\\n  -H "Content-Type: application/json" \\\n  -d \'{body_str}\''
        return f'curl -X {method} "{full_url}"'


def generate_js_code(method: str, url: str, params: dict = None, body: dict = None) -> str:
    """Generate JavaScript fetch code."""
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"
    else:
        full_url = url
    
    if method == "GET":
        return f'''fetch("{full_url}")
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));'''
    else:
        body_str = json.dumps(body, indent=2) if body else "{}"
        return f'''fetch("{full_url}", {{
  method: "{method}",
  headers: {{"Content-Type": "application/json"}},
  body: JSON.stringify({body_str})
}})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));'''


def run_python_code(code: str) -> str:
    """Execute Python code in sandbox with enhanced security and output."""
    output = io.StringIO()
    error_output = io.StringIO()
    
    # Create restricted globals with common modules
    safe_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "bool": bool,
            "True": True,
            "False": False,
            "None": None,
            "isinstance": isinstance,
            "type": type,
            "round": round,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "sorted": sorted,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "all": all,
            "any": any,
        },
        "requests": requests,
        "json": json,
        "pd": pd,
        "DataFrame": pd.DataFrame,
        "time": time,
    }
    
    start_time = time.time()
    
    # Validate code doesn't contain dangerous operations
    dangerous_patterns = ['__import__', 'eval', 'exec', 'compile', 'open', 'file']
    for pattern in dangerous_patterns:
        if pattern in code and pattern not in ['__import__']:
            return f"[Security Error]\nDangerous operation '{pattern}' is not allowed in sandbox.\n\n[Validation failed]"
    
    try:
        with redirect_stdout(output), redirect_stderr(error_output):
            exec(code, safe_globals, {})
        
        elapsed = time.time() - start_time
        result = output.getvalue()
        errors = error_output.getvalue()
        
        final_output = "[EXECUTION OUTPUT]\n" + "="*50 + "\n"
        
        if result:
            final_output += result
        else:
            final_output += "(No output)\n"
        
        if errors:
            final_output += f"\n[WARNINGS/ERRORS]\n{errors}"
        
        final_output += "\n" + "="*50
        final_output += f"\n Completed successfully in {elapsed:.3f}s"
        
        return final_output
    
    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        return f"[NETWORK ERROR]\n{str(e)}\n\nCheck that the API server is running and the URL is correct.\n\n Failed after {elapsed:.3f}s"
    
    except json.JSONDecodeError as e:
        elapsed = time.time() - start_time
        return f"[JSON ERROR]\n{str(e)}\n\nThe response was not valid JSON.\n\n Failed after {elapsed:.3f}s"
    
    except Exception as e:
        elapsed = time.time() - start_time
        error_lines = traceback.format_exc().split('\n')
        # Filter out internal exec() lines
        relevant_lines = [l for l in error_lines if '<string>' not in l or 'File' in l]
        return f"[RUNTIME ERROR]\n{''.join(relevant_lines)}\n Failed after {elapsed:.3f}s"


def search_endpoints(query: str) -> List[dict]:
    """Search endpoints by name, path, or description."""
    if not query:
        return []
    
    query_lower = query.lower()
    results = []
    
    for category, data in ENDPOINTS.items():
        for ep in data["endpoints"]:
            # Search in name, path, description
            if (query_lower in ep["name"].lower() or 
                query_lower in ep["path"].lower() or 
                query_lower in ep["description"].lower()):
                results.append({**ep, "category": category})
    
    return results[:10]  # Limit to 10 results


# ==============================================================================
# HEADER
# ==============================================================================
api_online = check_api_status()
status_class = "status-online" if api_online else "status-offline"
status_text = "Online" if api_online else "Offline"

st.markdown(f"""
<div class="header-bar">
    <div class="header-title">API EXPLORER</div>
    <div class="status-badge {status_class}">
        <span class="status-dot"></span>
        API {status_text}
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# GLOBAL SEARCH
# ==============================================================================
search_query = st.text_input(
    "Search APIs",
    placeholder="Search endpoints... (e.g., portfolio, var, quote)",
    label_visibility="collapsed",
    key="global_search"
)

if search_query:
    search_results = search_endpoints(search_query)
    if search_results:
        st.markdown("**Search Results:**")
        cols = st.columns(3)
        for i, result in enumerate(search_results):
            with cols[i % 3]:
                method_class = f"method-tag-{result['method'].lower()}"
                btn_label = f"[{result['method']}] {result['name']}"
                if st.button(btn_label, key=f"search_{i}", use_container_width=True):
                    st.session_state.selected_endpoint = {**result}
                    st.session_state.response_data = None
                    st.rerun()
        st.markdown("---")


# ==============================================================================
# MAIN LAYOUT
# ==============================================================================
left_col, right_col = st.columns([1, 3])


# ==============================================================================
# LEFT PANEL - Endpoint Collections
# ==============================================================================
with left_col:
    st.markdown("#### ENDPOINTS")
    
    # Filter within sidebar
    filter_text = st.text_input("Filter", placeholder="Filter...", label_visibility="collapsed", key="filter_endpoints")
    
    for category, data in ENDPOINTS.items():
        endpoints = data["endpoints"]
        
        # Apply filter
        if filter_text:
            endpoints = [ep for ep in endpoints if filter_text.lower() in ep["name"].lower() or filter_text.lower() in ep["path"].lower()]
            if not endpoints:
                continue
        
        # Category expander
        with st.expander(f"{category} ({len(endpoints)})", expanded=(category in st.session_state.expanded_categories)):
            for ep in endpoints:
                method = ep["method"]
                is_selected = (st.session_state.selected_endpoint and 
                              st.session_state.selected_endpoint.get("name") == ep["name"])
                
                # Button for each endpoint
                btn_type = "primary" if is_selected else "secondary"
                if st.button(
                    f"[{method}] {ep['name']}", 
                    key=f"ep_{category}_{ep['name']}", 
                    use_container_width=True,
                    type=btn_type
                ):
                    st.session_state.selected_endpoint = {**ep, "category": category}
                    st.session_state.response_data = None
                    st.session_state.expanded_categories.add(category)
                    st.rerun()
    
    # History section
    if st.session_state.request_history:
        st.markdown("---")
        st.markdown("#### HISTORY")
        for i, hist in enumerate(st.session_state.request_history[-5:][::-1]):
            if st.button(f"[{hist['method']}] {hist['path'][:20]}...", key=f"hist_{i}", use_container_width=True):
                st.session_state.selected_endpoint = hist["endpoint"]
                st.rerun()


# ==============================================================================
# RIGHT PANEL - Request Builder & Response
# ==============================================================================
with right_col:
    if st.session_state.selected_endpoint is None:
        # Welcome screen with instructions
        st.markdown("""
        <div style='text-align: center; padding: 40px 20px;'>
            <h2 style='color: #48bb78; margin-bottom: 20px;'>Welcome to API Explorer</h2>
            <p style='font-size: 16px; color: #a0aec0; max-width: 700px; margin: 0 auto 30px;'>
                A powerful Postman-style interface to test and explore all QuantLib Pro API endpoints.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick start guide
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 1⃣ Find Endpoint
            
            **Browse** the endpoint collections on the left panel, organized by category.
            
            **Or Search** using the search bar above to quickly find APIs by name or function.
            """)
        
        with col2:
            st.markdown("""
            ### 2⃣ Configure & Test
            
            **Edit Parameters** - Modify path params, query params, and request body.
            
            **Send Request** - Click the SEND button to execute and see real response data.
            """)
        
        with col3:
            st.markdown("""
            ### 3⃣ Generate Code
            
            **View Code** - Get production-ready Python, curl, or JavaScript code.
            
            **Run in Sandbox** - Execute Python code directly and see output in real-time.
            """)
        
        st.markdown("---")
        
        # Quick stats
        total_endpoints = sum(len(cat["endpoints"]) for cat in ENDPOINTS.values())
        categories = len(ENDPOINTS)
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            st.metric("Total Endpoints", total_endpoints)
        with stat_col2:
            st.metric("Categories", categories)
        with stat_col3:
            api_status = " Online" if check_api_status() else " Offline"
            st.metric("API Status", api_status)
        with stat_col4:
            history_count = len(st.session_state.request_history)
            st.metric("Requests Made", history_count)
        
        st.markdown("---")
        
        # Popular endpoints
        st.markdown("###  Popular Endpoints")
        
        popular = [
            ("Health", "Health Check"),
            ("Portfolio", "Optimize Portfolio"),
            ("Risk Analysis", "Value at Risk"),
            ("Options", "Black-Scholes Price"),
            ("Real-Time Data", "Get Quote"),
        ]
        
        cols = st.columns(5)
        for idx, (cat, ep_name) in enumerate(popular):
            with cols[idx]:
                # Find the endpoint
                for endpoint in ENDPOINTS[cat]["endpoints"]:
                    if endpoint["name"] == ep_name:
                        if st.button(f"{endpoint['method']}\n{ep_name}", key=f"popular_{idx}", use_container_width=True):
                            st.session_state.selected_endpoint = {**endpoint, "category": cat}
                            st.rerun()
                        break
        
        st.markdown("---")
        
        st.markdown("""
        **Features:**
        - Browse API endpoints by category
        - Build and send requests
        - View responses as JSON, tables, or charts
        - Generate code in Python, curl, or JavaScript
        - Run Python code directly in the browser
        """)
        
        # Quick start buttons
        st.markdown("#### Quick Start")
        qcols = st.columns(4)
        quick_endpoints = [
            ("Health Check", "Health", "Health Check"),
            ("Get Quote", "Real-Time Data", "Get Quote"),
            ("Optimize Portfolio", "Portfolio", "Optimize Portfolio"),
            ("Calculate VaR", "Risk Analysis", "Value at Risk"),
        ]
        for i, (label, cat, name) in enumerate(quick_endpoints):
            with qcols[i]:
                if st.button(label, use_container_width=True):
                    for ep in ENDPOINTS[cat]["endpoints"]:
                        if ep["name"] == name:
                            st.session_state.selected_endpoint = {**ep, "category": cat}
                            st.rerun()
    
    else:
        # Endpoint selected
        endpoint = st.session_state.selected_endpoint
        method = endpoint["method"]
        
        # URL Bar
        method_class = f"method-{method.lower()}"
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <span class="method-badge {method_class}">{method}</span>
            <span style="font-family: monospace; font-size: 14px; color: #c9d1d9;">{endpoint['name']}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(endpoint["description"])
        
        # Path parameters
        path = endpoint["path"]
        path_params = {}
        query_params = {}
        
        if endpoint.get("params"):
            param_cols = st.columns(len(endpoint["params"]))
            for i, param in enumerate(endpoint["params"]):
                with param_cols[i]:
                    value = st.text_input(
                        f"{param['type'].upper()}: {param['name']}",
                        value=param.get("default", ""),
                        help=param.get("description", ""),
                        key=f"param_{param['name']}"
                    )
                    if param["type"] == "path":
                        path_params[param["name"]] = value
                    else:
                        query_params[param["name"]] = value
        
        # Build URL
        final_url = build_url(path, path_params)
        url_display = final_url
        if query_params:
            qs = "&".join([f"{k}={v}" for k, v in query_params.items() if v])
            if qs:
                url_display += f"?{qs}"
        
        st.code(url_display, language=None)
        
        # Request body
        body_data = None
        json_valid = True
        if endpoint.get("body"):
            st.markdown("**Request Body**")
            default_body = json.dumps(endpoint["body"], indent=2)
            body_input = st.text_area(
                "JSON", 
                value=default_body, 
                height=150, 
                key="req_body", 
                label_visibility="collapsed",
                help="Edit the JSON body - validation happens on-the-fly"
            )
            try:
                body_data = json.loads(body_input)
                st.success(" Valid JSON")
            except json.JSONDecodeError as e:
                st.error(f" Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}")
                json_valid = False
                body_data = None
        
        # Send button
        btn_cols = st.columns([2, 1, 1])
        with btn_cols[0]:
            # Disable send if JSON is invalid
            can_send = json_valid or not endpoint.get("body")
            if can_send:
                send_clicked = st.button(" SEND REQUEST", type="primary", use_container_width=True)
            else:
                send_clicked = st.button(" SEND REQUEST", type="primary", use_container_width=True, disabled=True)
                st.caption(" Fix JSON errors before sending")
        with btn_cols[1]:
            if st.button(" Clear Response", use_container_width=True):
                st.session_state.response_data = None
                st.session_state.response_status = None
                st.session_state.code_output = None
                st.rerun()
        
        if send_clicked and can_send:
            with st.spinner(f"Sending {method} request to {final_url}..."):
                clean_qp = {k: v for k, v in query_params.items() if v} if query_params else None
                status, data, elapsed = execute_request(method, final_url, clean_qp, body_data)
                st.session_state.response_status = status
                st.session_state.response_data = data
                st.session_state.response_time = elapsed
                
                # Add to history (limit to last 20)
                history_entry = {
                    "method": method,
                    "path": path,
                    "url": final_url,
                    "endpoint": endpoint,
                    "timestamp": datetime.now().isoformat(),
                    "status": status
                }
                st.session_state.request_history.append(history_entry)
                if len(st.session_state.request_history) > 20:
                    st.session_state.request_history = st.session_state.request_history[-20:]
                
                # Show toast notification
                if status == 0:
                    st.toast(" Request failed - check connection", icon="")
                elif 200 <= status < 300:
                    st.toast(f" Success! {status} in {elapsed:.0f}ms", icon="")
                else:
                    st.toast(f" Error {status}", icon="")
        
        # Response section
        if st.session_state.response_data is not None:
            st.markdown("---")
            st.markdown("###  Response")
            
            # Status bar
            status = st.session_state.response_status
            elapsed = st.session_state.response_time
            
            stat_cols = st.columns([1, 1, 1, 1])
            with stat_cols[0]:
                if status == 0:
                    st.error(" Connection Error")
                elif 200 <= status < 300:
                    st.success(f" {status} OK")
                elif 400 <= status < 500:
                    st.warning(f" {status} Client Error")
                elif 500 <= status < 600:
                    st.error(f" {status} Server Error")
                else:
                    st.info(f"ℹ {status}")
            
            with stat_cols[1]:
                if elapsed < 100:
                    st.success(f" {elapsed:.0f} ms")
                elif elapsed < 1000:
                    st.info(f"⏱ {elapsed:.0f} ms")
                else:
                    st.warning(f" {elapsed:.0f} ms")
            
            with stat_cols[2]:
                size = len(json.dumps(st.session_state.response_data))
                if size < 1024:
                    st.info(f" {size} B")
                elif size < 1024*1024:
                    st.info(f" {size/1024:.1f} KB")
                else:
                    st.info(f" {size/(1024*1024):.1f} MB")
            
            with stat_cols[3]:
                # Copy response button
                if st.button(" Copy JSON", use_container_width=True):
                    st.toast("Response copied to clipboard!", icon="")
            
            # Check if this is an error response
            data = st.session_state.response_data
            is_error = status == 0 or status >= 400 or (isinstance(data, dict) and "error" in data)
            
            if is_error and isinstance(data, dict):
                # Show error details prominently
                st.error("**Error Response**")
                if "error" in data:
                    st.markdown(f"**Error Type:** `{data.get('error')}`")
                if "message" in data:
                    st.markdown(f"**Message:** {data.get('message')}")
                if "suggestion" in data:
                    st.info(f" **Suggestion:** {data.get('suggestion')}")
                if "detail" in data:
                    st.markdown(f"**Details:** {data.get('detail')}")
            
            # Response tabs
            resp_tabs = st.tabs([" JSON", " Table", " Chart"])
            
            with resp_tabs[0]:
                st.json(st.session_state.response_data)
            
            with resp_tabs[1]:
                try:
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True, height=400)
                        st.caption(f"Showing {len(df)} rows")
                    elif isinstance(data, dict):
                        # Find arrays in response
                        found_array = False
                        for key, val in data.items():
                            if isinstance(val, list) and len(val) > 0:
                                st.markdown(f"**{key}:**")
                                df = pd.DataFrame(val)
                                st.dataframe(df, use_container_width=True, height=300)
                                st.caption(f"Showing {len(df)} rows")
                                found_array = True
                                break
                        
                        if not found_array:
                            # Show dict as single-row table
                            df = pd.DataFrame([data])
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No tabular data in response")
                except Exception as e:
                    st.warning(f"Could not convert to table: {str(e)}")
            
            with resp_tabs[2]:
                try:
                    chart_created = False
                    
                    if isinstance(data, dict):
                        # Portfolio weights
                        if "weights" in data and isinstance(data["weights"], dict):
                            fig = px.pie(
                                names=list(data["weights"].keys()), 
                                values=list(data["weights"].values()), 
                                title="Portfolio Weights"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            chart_created = True
                        
                        # Metrics bar chart
                        elif any(k in data for k in ["var", "cvar", "sharpe", "volatility", "return", "alpha", "beta"]):
                            metrics = {k: v for k, v in data.items() if isinstance(v, (int, float))}
                            if metrics:
                                fig = px.bar(
                                    x=list(metrics.keys()), 
                                    y=list(metrics.values()), 
                                    title="Metrics",
                                    labels={"x": "Metric", "y": "Value"}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                chart_created = True
                        
                        # Time series data
                        elif "dates" in data and any(k in data for k in ["prices", "values", "returns"]):
                            dates = data.get("dates", [])
                            for key in ["prices", "values", "returns"]:
                                if key in data:
                                    fig = px.line(
                                        x=dates, 
                                        y=data[key], 
                                        title=f"{key.title()} Over Time",
                                        labels={"x": "Date", "y": key.title()}
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                    chart_created = True
                                    break
                    
                    if not chart_created:
                        st.info(" No chartable data detected. Charts work best with:\n- Portfolio weights (dict)\n- Numeric metrics (var, sharpe, etc.)\n- Time series (dates + prices/values)")
                
                except Exception as e:
                    st.warning(f"Could not create chart: {str(e)}")
        
        
        # Code Playground
        st.markdown("---")
        st.markdown("#### CODE PLAYGROUND")
        
        # Info box
        st.info(" **Tip:** Parameters are clearly marked in sections. Edit the values in `params`, `payload`, etc. then click RUN CODE to test.")
        
        lang_col, action_col = st.columns([1, 3])
        with lang_col:
            lang = st.selectbox("Language", ["Python", "curl", "JavaScript"], label_visibility="collapsed")
        
        # Generate code based on language
        clean_qp = {k: v for k, v in query_params.items() if v} if query_params else None
        if lang == "Python":
            generated_code = generate_python_code(method, final_url, clean_qp, body_data)
        elif lang == "curl":
            generated_code = generate_curl_code(method, final_url, clean_qp, body_data)
        else:
            generated_code = generate_js_code(method, final_url, clean_qp, body_data)
        
        # Side by side: Code Editor | Output
        code_col, output_col = st.columns(2)
        
        with code_col:
            st.markdown("**Code Editor** ")
            code_input = st.text_area(
                "code_editor",
                value=generated_code,
                height=350,
                key="code_editor",
                label_visibility="collapsed",
                help="Edit parameters in the sections marked with '===== PARAMETERS ====='"
            )
            
            run_col, reset_col = st.columns(2)
            with run_col:
                if lang == "Python":
                    run_clicked = st.button("▶ RUN CODE", type="primary", use_container_width=True)
                else:
                    run_clicked = False
                    st.button("▶ RUN CODE", disabled=True, use_container_width=True, help="Only Python can be executed in sandbox")
            with reset_col:
                if st.button(" Reset to Original", use_container_width=True):
                    st.session_state.code_output = None
                    st.rerun()
            
            if run_clicked:
                if not code_input.strip():
                    st.error("Code editor is empty!")
                else:
                    with st.spinner("Executing code..."):
                        try:
                            output = run_python_code(code_input)
                            st.session_state.code_output = output
                        except Exception as e:
                            st.session_state.code_output = f"[EXECUTION ERROR]\n{str(e)}"
        
        with output_col:
            st.markdown("**Execution Output** ")
            if st.session_state.code_output:
                # Color-code based on success/failure
                if "" in st.session_state.code_output:
                    st.success("Execution successful!")
                elif "" in st.session_state.code_output:
                    st.error("Execution failed - see details below")
                
                st.code(st.session_state.code_output, language="text")
            else:
                st.code(
                    "# No output yet\n"
                    "# \n"
                    "# Click 'RUN CODE' to execute the Python code\n"
                    "# Output will display here with:\n"
                    "#   - Response data\n"
                    "#   - Status codes\n"
                    "#   - Error messages (if any)\n"
                    "#   - Execution time",
                    language="text"
                )


# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 12px;'>"
    f"QuantLib Pro API Explorer | "
    f"<a href='{API_BASE}/docs' target='_blank'>OpenAPI Docs</a> | "
    f"<a href='{API_BASE}/redoc' target='_blank'>ReDoc</a>"
    f"</div>",
    unsafe_allow_html=True
)
