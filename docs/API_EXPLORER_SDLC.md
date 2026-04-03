# API Explorer - Software Development Life Cycle Documentation

## Document Control

| Attribute | Value |
|-----------|-------|
| **Document ID** | SDLC-APIEXP-001 |
| **Version** | 1.1.0 |
| **Status** | Implementation Complete |
| **Created** | February 26, 2026 |
| **Last Updated** | February 26, 2026 |
| **Author** | QuantLib Pro Engineering Team |
| **Reviewers** | Architecture Team, QA Team, Product Owner |
| **Design Principle** | Professional UI - No emoji icons (text/CSS badges only) |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Phase 1: Requirements Analysis](#2-phase-1-requirements-analysis)
3. [Phase 2: System Design](#3-phase-2-system-design)
4. [Phase 3: Implementation](#4-phase-3-implementation)
5. [Phase 4: Testing](#5-phase-4-testing)
6. [Phase 5: Deployment](#6-phase-5-deployment)
7. [Phase 6: Maintenance](#7-phase-6-maintenance)
8. [Risk Assessment](#8-risk-assessment)
9. [Appendices](#9-appendices)

---

## 1. Executive Summary

### 1.1 Project Overview

The **API Explorer** is a Postman-like interactive dashboard embedded within the QuantLib Pro Streamlit application. It enables users to discover, test, and execute API endpoints, generate code snippets, and visualize responses—all without leaving the application.

### 1.2 Business Objectives

| Objective | Description | Success Metric |
|-----------|-------------|----------------|
| **Developer Productivity** | Reduce time to test API endpoints | 70% reduction in API testing time |
| **Discoverability** | Make all 60+ endpoints easily searchable | < 3 seconds to find any endpoint |
| **Code Generation** | Auto-generate production-ready code | Support Python, curl, JavaScript |
| **Self-Service** | Eliminate need for external tools like Postman | 90% of API testing done in-app |

### 1.3 Scope

#### In Scope
- Interactive API endpoint browser
- Request builder with parameter editing
- Response visualization (JSON, Table, Chart)
- Code generation and execution playground
- Search and filter functionality
- Request history
- Responsive design

#### Out of Scope
- API endpoint creation/modification
- Authentication management UI
- API versioning controls
- Rate limit configuration

### 1.4 Stakeholders

| Role | Responsibility |
|------|----------------|
| Product Owner | Feature prioritization, acceptance criteria |
| Backend Engineers | API endpoint documentation, schema validation |
| Frontend Engineers | Streamlit UI implementation |
| QA Engineers | Test case development, execution |
| DevOps | Deployment, monitoring |
| End Users | Quant developers, data scientists, traders |

---

## 2. Phase 1: Requirements Analysis

### 2.1 Functional Requirements

#### FR-001: Endpoint Discovery
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-001.1 | Display all API endpoints organized by category | P0 |  Approved |
| FR-001.2 | Show endpoint count per category | P1 |  Approved |
| FR-001.3 | Indicate HTTP method with color-coding | P0 |  Approved |
| FR-001.4 | Display endpoint description and path | P0 |  Approved |

#### FR-002: Search & Filter
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-002.1 | Global search bar at top of page | P0 |  Approved |
| FR-002.2 | Fuzzy matching on name, path, description | P0 |  Approved |
| FR-002.3 | Search results grouped by category | P1 |  Approved |
| FR-002.4 | Keyboard shortcut (Ctrl+K) to focus search | P2 |  Approved |
| FR-002.5 | Filter within sidebar endpoint list | P1 |  Approved |

#### FR-003: Request Builder
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-003.1 | Editable URL bar with method selector | P0 |  Approved |
| FR-003.2 | Path parameter input fields | P0 |  Approved |
| FR-003.3 | Query parameter input fields | P0 |  Approved |
| FR-003.4 | JSON body editor with syntax highlighting | P0 |  Approved |
| FR-003.5 | JSON validation with error messages | P1 |  Approved |
| FR-003.6 | Headers configuration tab | P2 |  Planned |

#### FR-004: Request Execution
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-004.1 | Send button to execute request | P0 |  Approved |
| FR-004.2 | Loading indicator during request | P0 |  Approved |
| FR-004.3 | Display response status code | P0 |  Approved |
| FR-004.4 | Display response time (ms) | P0 |  Approved |
| FR-004.5 | Display response size (bytes) | P1 |  Approved |
| FR-004.6 | Connection error handling | P0 |  Approved |

#### FR-005: Response Visualization
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-005.1 | JSON view with syntax highlighting | P0 |  Approved |
| FR-005.2 | Table view for array/object data | P1 |  Approved |
| FR-005.3 | Chart view for numeric data | P2 |  Approved |
| FR-005.4 | Copy response to clipboard | P1 |  Approved |

#### FR-006: Code Generation
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-006.1 | Generate Python requests code | P0 |  Approved |
| FR-006.2 | Generate curl command | P0 |  Approved |
| FR-006.3 | Generate JavaScript fetch code | P1 |  Approved |
| FR-006.4 | Copy code to clipboard | P0 |  Approved |

#### FR-007: Code Playground
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-007.1 | Editable code area | P0 |  Approved |
| FR-007.2 | Run Python code button | P0 |  Approved |
| FR-007.3 | Display execution output | P0 |  Approved |
| FR-007.4 | Side-by-side code and output layout | P1 |  Approved |
| FR-007.5 | Reset code to original | P1 |  Approved |
| FR-007.6 | Execution time display | P2 |  Approved |

#### FR-008: History
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-008.1 | Store last N requests in session | P1 |  Approved |
| FR-008.2 | Display recent requests in sidebar | P1 |  Approved |
| FR-008.3 | Click to replay request | P1 |  Approved |

#### FR-009: Responsive Design
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-009.1 | Desktop layout (>1024px): side-by-side | P0 |  Approved |
| FR-009.2 | Tablet layout (<1024px): stacked | P1 |  Approved |
| FR-009.3 | Collapsible sidebar | P1 |  Approved |

### 2.2 Non-Functional Requirements

#### NFR-001: Performance
| ID | Requirement | Target | Validation |
|----|-------------|--------|------------|
| NFR-001.1 | Page load time | < 2 seconds | Load testing |
| NFR-001.2 | Search response time | < 100ms | Profiling |
| NFR-001.3 | Code generation time | < 50ms | Unit tests |

#### NFR-002: Usability
| ID | Requirement | Target | Validation |
|----|-------------|--------|------------|
| NFR-002.1 | Time to find endpoint | < 3 seconds | User testing |
| NFR-002.2 | Time to execute first request | < 30 seconds | User testing |
| NFR-002.3 | Error message clarity | 100% actionable | UX review |

#### NFR-003: Reliability
| ID | Requirement | Target | Validation |
|----|-------------|--------|------------|
| NFR-003.1 | Uptime | 99.9% | Monitoring |
| NFR-003.2 | Error recovery | Graceful degradation | Chaos testing |

#### NFR-004: Security
| ID | Requirement | Target | Validation |
|----|-------------|--------|------------|
| NFR-004.1 | Code execution sandbox | No system access | Security audit |
| NFR-004.2 | Input sanitization | All user inputs | Penetration testing |

### 2.3 User Stories

```gherkin
Feature: API Explorer

  @search @P0
  Scenario: User searches for an endpoint
    Given I am on the API Explorer page
    When I type "portfolio" in the search bar
    Then I see endpoints matching "portfolio"
    And results are grouped by category
    And I can click to select an endpoint

  @request @P0
  Scenario: User executes a GET request
    Given I have selected the "Health Check" endpoint
    When I click the "Send" button
    Then I see a loading indicator
    And the response displays with status 200
    And response time is shown in milliseconds

  @request @P0
  Scenario: User executes a POST request with body
    Given I have selected the "Optimize Portfolio" endpoint
    And I have entered valid JSON in the body
    When I click the "Send" button
    Then the request is sent with the JSON body
    And the response is displayed

  @code @P0
  Scenario: User generates Python code
    Given I have selected an endpoint
    And I have configured parameters
    When I view the Code tab
    Then I see Python code using requests library
    And I can copy the code to clipboard

  @playground @P0
  Scenario: User runs code in playground
    Given I have generated code for an endpoint
    When I click "Run Code"
    Then the code executes
    And output displays next to the code
    And execution time is shown

  @history @P1
  Scenario: User replays a previous request
    Given I have executed several requests
    When I click a request in the History section
    Then the endpoint is loaded
    And previous parameters are restored
```

### 2.4 Acceptance Criteria

| Criterion | Description | Test Method |
|-----------|-------------|-------------|
| AC-001 | All 60+ endpoints are accessible | Automated |
| AC-002 | Search returns results in < 100ms | Performance |
| AC-003 | Generated code executes successfully | Integration |
| AC-004 | Responsive layout works on tablet | Manual |
| AC-005 | Error states display clear messages | Manual |

---

## 3. Phase 2: System Design

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Streamlit Page                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│  │  │ Search   │ │ Endpoint │ │ Request  │ │ Response │        │   │
│  │  │ Component│ │ Sidebar  │ │ Builder  │ │ Viewer   │        │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│  │  ┌──────────────────────────────────────────────────┐       │   │
│  │  │              Code Playground                      │       │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐        │       │   │
│  │  │  │  Code Editor    │  │  Output Panel   │        │       │   │
│  │  │  └─────────────────┘  └─────────────────┘        │       │   │
│  │  └──────────────────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BUSINESS LOGIC LAYER                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ Endpoint     │ │ Request      │ │ Code         │                │
│  │ Catalog      │ │ Executor     │ │ Generator    │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ Search       │ │ Response     │ │ Code         │                │
│  │ Engine       │ │ Formatter    │ │ Executor     │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ Session      │ │ HTTP         │ │ Endpoint     │                │
│  │ State        │ │ Client       │ │ Definitions  │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Backend                            │  │
│  │              http://localhost:8000                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Design

#### 3.2.1 Endpoint Catalog

```python
ENDPOINTS = {
    "category_name": {
        # Note: Icons removed for professional UI - using CSS badges instead
        "endpoints": [
            {
                "name": "Human-readable name",
                "method": "GET|POST|PUT|DELETE",
                "path": "/api/v1/path/{param}",
                "description": "What this endpoint does",
                "params": [
                    {
                        "name": "param_name",
                        "type": "path|query|header",
                        "required": True|False,
                        "default": "value",
                        "description": "Parameter description"
                    }
                ],
                "body": {
                    "field": "default_value"
                }
            }
        ]
    }
}
```

#### 3.2.2 Search Engine

```python
class SearchEngine:
    """Fuzzy search across endpoints."""
    
    def __init__(self, endpoints: Dict):
        self.index = self._build_index(endpoints)
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search endpoints by name, path, description, tags.
        Returns results sorted by relevance score.
        """
        pass
    
    def _build_index(self, endpoints: Dict) -> SearchIndex:
        """Build inverted index for fast lookup."""
        pass
    
    def _fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score (0-1)."""
        pass
```

#### 3.2.3 Request Executor

```python
class RequestExecutor:
    """Execute HTTP requests with error handling."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    def execute(
        self,
        method: str,
        path: str,
        params: Dict = None,
        body: Dict = None,
        headers: Dict = None
    ) -> RequestResult:
        """
        Execute request and return result with timing.
        
        Returns:
            RequestResult with status, data, elapsed_ms, size_bytes
        """
        pass
```

#### 3.2.4 Code Generator

```python
class CodeGenerator:
    """Generate code snippets for different languages."""
    
    LANGUAGES = ["python", "curl", "javascript", "httpx", "aiohttp"]
    
    def generate(
        self,
        language: str,
        method: str,
        url: str,
        params: Dict = None,
        body: Dict = None,
        headers: Dict = None
    ) -> str:
        """Generate executable code snippet."""
        pass
    
    def _generate_python(self, ...) -> str:
        pass
    
    def _generate_curl(self, ...) -> str:
        pass
    
    def _generate_javascript(self, ...) -> str:
        pass
```

#### 3.2.5 Code Executor

```python
class CodeExecutor:
    """Safely execute Python code in sandbox."""
    
    ALLOWED_MODULES = ["requests", "json", "pandas", "numpy"]
    TIMEOUT_SECONDS = 30
    
    def execute(self, code: str) -> ExecutionResult:
        """
        Execute code and capture output.
        
        Returns:
            ExecutionResult with stdout, stderr, elapsed, success
        """
        pass
    
    def _create_sandbox(self) -> Dict:
        """Create restricted execution environment."""
        pass
```

### 3.3 Data Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│  Search  │────▶│  Select  │────▶│  Build   │
│  Input   │     │  Query   │     │  Endpoint│     │  Request │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                         │
                                                         ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  View    │◀────│  Format  │◀────│  Receive │◀────│  Send    │
│  Response│     │  Response│     │  Response│     │  Request │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
      │
      ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Generate│────▶│  Edit    │────▶│  Execute │
│  Code    │     │  Code    │     │  Code    │
└──────────┘     └──────────┘     └──────────┘
                                        │
                                        ▼
                                  ┌──────────┐
                                  │  Display │
                                  │  Output  │
                                  └──────────┘
```

### 3.4 UI Layout Specification

#### Desktop Layout (>1024px)

```
┌─────────────────────────────────────────────────────────────────────┐
│ HEADER (60px)                                                       │
│ [Logo] API Explorer                           [* Online] [Settings] │
├─────────────────────────────────────────────────────────────────────┤
│ SEARCH BAR (50px)                                                   │
│ [Search APIs... ]                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ URL BAR (50px)                                                      │
│ [METHOD ▼] [URL INPUT                                   ] [ SEND] │
├────────────────┬────────────────────────────────────────────────────┤
│ SIDEBAR (250px)│ MAIN CONTENT                                       │
│                │ ┌────────────────────────────────────────────────┐ │
│ [Filter...]    │ │ REQUEST (200px)                                │ │
│                │ │ [Params] [Headers] [Body]                      │ │
│ ▼ Category 1   │ │ ┌────────────────────────────────────────────┐ │ │
│   ○ Endpoint   │ │ │ JSON Editor                                │ │ │
│   ○ Endpoint   │ │ └────────────────────────────────────────────┘ │ │
│                │ ├────────────────────────────────────────────────┤ │
│ ▼ Category 2   │ │ RESPONSE (200px)                               │ │
│   ● Selected   │ │ [Status] [Time] [Size]                         │ │
│   ○ Endpoint   │ │ [JSON] [Table] [Chart]                         │ │
│                │ │ ┌────────────────────────────────────────────┐ │ │
│ ▶ Category 3   │ │ │ Response Data                              │ │ │
│                │ │ └────────────────────────────────────────────┘ │ │
│ ───────────    │ ├────────────────────────────────────────────────┤ │
│  HISTORY     │ │ CODE PLAYGROUND (250px)                        │ │
│  POST /api.. │ │ [Python ▼] [ Copy] [▶ RUN] [ Reset]       │ │
│  GET /api..  │ │ ┌───────────────────┬────────────────────────┐ │ │
│                │ │ │ CODE EDITOR       │ OUTPUT                 │ │ │
│                │ │ │ (50%)             │ (50%)                  │ │ │
│                │ │ │                   │                        │ │ │
│                │ │ │ import requests   │ {'status': 'ok'}       │ │ │
│                │ │ │ ...               │  Done 0.45s          │ │ │
│                │ │ └───────────────────┴────────────────────────┘ │ │
│                │ └────────────────────────────────────────────────┘ │
└────────────────┴────────────────────────────────────────────────────┘
```

#### Tablet Layout (<1024px)

```
┌─────────────────────────────────┐
│ HEADER (50px)                   │
│ [=] API Explorer  [*] [Cfg]     │
├─────────────────────────────────┤
│ SEARCH (50px)                   │
│ [Search APIs...]                │
├─────────────────────────────────┤
│ URL BAR (50px)                  │
│ [POST v] /api/v1/...  [SEND]    │
├─────────────────────────────────┤
│ ENDPOINTS (Collapsible, 150px)  │
│ [▲ Collapse]                    │
│ ● Optimize Portfolio            │
│ ○ Efficient Frontier            │
│ ○ Value at Risk                 │
│ [Show all 25...]                │
├─────────────────────────────────┤
│ REQUEST (150px)                 │
│ [Params] [Body]                 │
│ ┌─────────────────────────────┐ │
│ │ {"tickers": [...]}          │ │
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ RESPONSE (150px)                │
│  200  ⏱ 234ms                │
│ [JSON] [Table]                  │
│ ┌─────────────────────────────┐ │
│ │ {"weights": {...}}          │ │
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ CODE (150px)                    │
│ [ Python ▼] [▶ RUN]          │
│ ┌─────────────────────────────┐ │
│ │ import requests             │ │
│ │ ...                         │ │
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ OUTPUT (100px)                  │
│ ┌─────────────────────────────┐ │
│ │ {'status': 'ok'}            │ │
│ │  Done 0.45s               │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### 3.5 State Management

```python
# Streamlit Session State Schema
session_state = {
    # Current endpoint
    "selected_endpoint": {
        "category": str,
        "name": str,
        "method": str,
        "path": str,
        ...
    },
    
    # Request state
    "path_params": Dict[str, str],
    "query_params": Dict[str, str],
    "request_body": str,  # JSON string
    "request_headers": Dict[str, str],
    
    # Response state
    "response_data": Any,
    "response_status": int,
    "response_time": float,  # ms
    "response_size": int,    # bytes
    
    # Code playground
    "code_language": str,    # python, curl, javascript
    "code_content": str,     # Editable code
    "code_output": str,      # Execution output
    "code_error": str,       # Error message if any
    
    # History
    "request_history": List[Dict],  # Last 20 requests
    
    # UI state
    "sidebar_collapsed": bool,
    "search_query": str,
    "search_results": List[Dict],
}
```

### 3.6 API Contract

#### Endpoint Definition Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Human-readable endpoint name"
    },
    "method": {
      "type": "string",
      "enum": ["GET", "POST", "PUT", "DELETE"]
    },
    "path": {
      "type": "string",
      "description": "URL path with {param} placeholders"
    },
    "description": {
      "type": "string",
      "description": "What this endpoint does"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Search keywords"
    },
    "params": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "type": {"enum": ["path", "query", "header"]},
          "required": {"type": "boolean"},
          "default": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["name", "type"]
      }
    },
    "body": {
      "type": "object",
      "description": "Default request body (null for GET)"
    }
  },
  "required": ["name", "method", "path"]
}
```

---

## 4. Phase 3: Implementation

### 4.1 Technology Stack

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| UI Framework | Streamlit | 1.32+ | Existing app framework |
| HTTP Client | requests | 2.31+ | Simple, reliable |
| Data Processing | pandas | 2.0+ | Table rendering |
| Visualization | plotly | 5.18+ | Interactive charts |
| JSON | json (stdlib) | - | Built-in |
| Fuzzy Search | fuzzywuzzy | 0.18+ | Fast fuzzy matching |

### 4.2 File Structure

```
pages/
└── 17_API_Explorer.py          # Main page (~800 lines)

quantlib_pro/
└── api_explorer/
    ├── __init__.py
    ├── catalog.py              # Endpoint definitions
    ├── search.py               # Search engine
    ├── executor.py             # Request execution
    ├── generator.py            # Code generation
    ├── playground.py           # Code sandbox
    └── formatters.py           # Response formatting
```

### 4.3 Implementation Tasks

| ID | Task | Estimate | Dependencies | Assignee |
|----|------|----------|--------------|----------|
| IMP-001 | Create endpoint catalog | 2h | - | TBD |
| IMP-002 | Build search engine | 3h | IMP-001 | TBD |
| IMP-003 | Implement URL bar component | 2h | - | TBD |
| IMP-004 | Build request builder | 4h | IMP-001 | TBD |
| IMP-005 | Implement request executor | 2h | - | TBD |
| IMP-006 | Build response viewer | 3h | IMP-005 | TBD |
| IMP-007 | Create code generator | 3h | IMP-004 | TBD |
| IMP-008 | Build code playground | 4h | IMP-007 | TBD |
| IMP-009 | Implement responsive CSS | 3h | All | TBD |
| IMP-010 | Add history feature | 2h | IMP-005 | TBD |
| IMP-011 | Integration testing | 4h | All | TBD |
| **Total** | | **32h** | | |

### 4.4 Code Standards

#### Python Style
- Follow PEP 8
- Type hints required
- Docstrings for all public functions
- Max function length: 50 lines

#### Naming Conventions
```python
# Classes: PascalCase
class RequestExecutor:
    pass

# Functions: snake_case
def execute_request():
    pass

# Constants: UPPER_SNAKE_CASE
API_BASE_URL = "http://localhost:8000"

# Session state keys: snake_case
st.session_state.selected_endpoint
```

### 4.5 Key Implementation Details

#### 4.5.1 Fuzzy Search Implementation

```python
from fuzzywuzzy import fuzz
from typing import List, Dict

def search_endpoints(query: str, endpoints: Dict, limit: int = 10) -> List[Dict]:
    """
    Fuzzy search across all endpoints.
    
    Scores:
    - Exact match in name: 100 points
    - Partial match in name: 80 points * ratio
    - Match in path: 60 points * ratio
    - Match in description: 40 points * ratio
    - Match in tags: 50 points * ratio
    """
    results = []
    query_lower = query.lower()
    
    for category, data in endpoints.items():
        for endpoint in data["endpoints"]:
            score = 0
            
            # Name matching
            name_ratio = fuzz.partial_ratio(query_lower, endpoint["name"].lower())
            if name_ratio == 100:
                score += 100
            else:
                score += 0.8 * name_ratio
            
            # Path matching
            path_ratio = fuzz.partial_ratio(query_lower, endpoint["path"].lower())
            score += 0.6 * path_ratio
            
            # Description matching
            desc_ratio = fuzz.partial_ratio(query_lower, endpoint.get("description", "").lower())
            score += 0.4 * desc_ratio
            
            # Tags matching
            for tag in endpoint.get("tags", []):
                tag_ratio = fuzz.ratio(query_lower, tag.lower())
                score += 0.5 * tag_ratio
            
            if score > 50:  # Threshold
                results.append({
                    "endpoint": endpoint,
                    "category": category,
                    "score": score
                })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
```

#### 4.5.2 Safe Code Execution

```python
import sys
import io
import contextlib
from typing import Tuple

def execute_code_safely(code: str, timeout: int = 30) -> Tuple[str, str, bool]:
    """
    Execute Python code in a restricted environment.
    
    Returns:
        (stdout, stderr, success)
    """
    # Allowed imports
    allowed_globals = {
        "__builtins__": {
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
            "isinstance": isinstance,
            "type": type,
            "True": True,
            "False": False,
            "None": None,
        },
        "requests": __import__("requests"),
        "json": __import__("json"),
        "pd": __import__("pandas"),
        "np": __import__("numpy"),
    }
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(stdout_capture):
            with contextlib.redirect_stderr(stderr_capture):
                exec(code, allowed_globals, {})
        
        return stdout_capture.getvalue(), stderr_capture.getvalue(), True
    
    except Exception as e:
        return "", f"{type(e).__name__}: {str(e)}", False
```

---

## 5. Phase 4: Testing

### 5.1 Test Strategy

| Test Type | Coverage Target | Tools |
|-----------|-----------------|-------|
| Unit Tests | 80% code coverage | pytest |
| Integration Tests | All endpoints | pytest + requests |
| UI Tests | Critical paths | Streamlit testing |
| Performance Tests | < 100ms search | locust |
| Security Tests | Code sandbox | Manual + automated |

### 5.2 Unit Test Cases

```python
# test_search.py
class TestSearchEngine:
    def test_exact_match_returns_highest_score(self):
        """Exact name match should score 100."""
        results = search_endpoints("Health Check", ENDPOINTS)
        assert results[0]["endpoint"]["name"] == "Health Check"
        assert results[0]["score"] >= 100
    
    def test_fuzzy_match_finds_partial(self):
        """Partial match should find endpoint."""
        results = search_endpoints("portf", ENDPOINTS)
        assert any("Portfolio" in r["endpoint"]["name"] for r in results)
    
    def test_path_search(self):
        """Search by path should work."""
        results = search_endpoints("/api/v1/risk", ENDPOINTS)
        assert any("Risk" in r["category"] for r in results)
    
    def test_empty_query_returns_empty(self):
        """Empty query should return empty results."""
        results = search_endpoints("", ENDPOINTS)
        assert results == []
    
    def test_no_match_returns_empty(self):
        """Non-matching query should return empty."""
        results = search_endpoints("xyznonexistent123", ENDPOINTS)
        assert results == []


# test_executor.py
class TestRequestExecutor:
    def test_get_request_success(self):
        """GET request should return status and data."""
        status, data, elapsed = execute_request("GET", "/health")
        assert status == 200
        assert "status" in data
        assert elapsed > 0
    
    def test_post_request_with_body(self):
        """POST request should send body."""
        body = {"tickers": ["AAPL"]}
        status, data, elapsed = execute_request("POST", "/api/v1/portfolio/optimize", body=body)
        assert status in [200, 422]  # Success or validation error
    
    def test_connection_error_handled(self):
        """Connection error should return graceful error."""
        status, data, elapsed = execute_request("GET", "http://localhost:9999/fake")
        assert status == 0
        assert "error" in data


# test_generator.py
class TestCodeGenerator:
    def test_python_get_generation(self):
        """Python GET code should be valid."""
        code = generate_python_code("GET", "http://localhost:8000/health")
        assert "import requests" in code
        assert "requests.get" in code
    
    def test_python_post_with_body(self):
        """Python POST code should include body."""
        body = {"key": "value"}
        code = generate_python_code("POST", "http://localhost:8000/api", body=body)
        assert "requests.post" in code
        assert "json=" in code
    
    def test_curl_generation(self):
        """curl command should be valid."""
        code = generate_curl_code("POST", "http://localhost:8000/api", body={"a": 1})
        assert "curl -X POST" in code
        assert "-H \"Content-Type: application/json\"" in code
    
    def test_javascript_generation(self):
        """JavaScript fetch code should be valid."""
        code = generate_javascript_code("GET", "http://localhost:8000/api")
        assert "fetch(" in code
        assert ".then(" in code


# test_playground.py
class TestCodePlayground:
    def test_simple_print(self):
        """Simple print should capture output."""
        stdout, stderr, success = execute_code_safely("print('hello')")
        assert success
        assert "hello" in stdout
    
    def test_requests_allowed(self):
        """requests library should be available."""
        code = "import requests; print(type(requests))"
        stdout, stderr, success = execute_code_safely(code)
        assert success
    
    def test_dangerous_imports_blocked(self):
        """Dangerous imports should be blocked."""
        code = "import os; os.system('echo pwned')"
        stdout, stderr, success = execute_code_safely(code)
        assert not success
    
    def test_syntax_error_handled(self):
        """Syntax errors should be caught."""
        code = "print('unclosed"
        stdout, stderr, success = execute_code_safely(code)
        assert not success
        assert "SyntaxError" in stderr
```

### 5.3 Integration Test Cases

```python
# test_integration.py
class TestAPIExplorerIntegration:
    @pytest.fixture
    def app(self):
        """Create Streamlit app instance."""
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file("pages/17_API_Explorer.py")
    
    def test_page_loads(self, app):
        """Page should load without errors."""
        app.run()
        assert not app.exception
    
    def test_search_shows_results(self, app):
        """Search should display matching endpoints."""
        app.run()
        app.text_input[0].set_value("portfolio").run()
        # Check that results are displayed
        assert "Portfolio" in app.markdown[0].value
    
    def test_endpoint_selection(self, app):
        """Selecting endpoint should populate request builder."""
        app.run()
        app.button[0].click().run()  # Click first endpoint
        # URL should be populated
        assert "/api/v1" in app.code[0].value
    
    def test_send_request(self, app):
        """Send button should execute request."""
        app.run()
        app.button("Health Check").click().run()
        app.button(" SEND").click().run()
        # Response should appear
        assert "200" in str(app.success)
    
    def test_code_generation(self, app):
        """Code tab should show generated code."""
        app.run()
        app.button("Health Check").click().run()
        # Code should be present
        assert "import requests" in str(app.code)
```

### 5.4 Performance Test Plan

```python
# locustfile.py
from locust import HttpUser, task, between

class APIExplorerUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(5)
    def search_endpoints(self):
        """Simulate search operations."""
        queries = ["portfolio", "risk", "var", "options", "health"]
        for q in queries:
            self.client.get(f"/search?q={q}")
    
    @task(3)
    def execute_get_request(self):
        """Simulate GET request execution."""
        self.client.get("/health")
    
    @task(2)
    def execute_post_request(self):
        """Simulate POST request execution."""
        self.client.post(
            "/api/v1/portfolio/optimize",
            json={"tickers": ["AAPL"], "budget": 100000}
        )
```

### 5.5 Test Execution Schedule

| Phase | Tests | Duration | Gate |
|-------|-------|----------|------|
| Pre-commit | Unit tests | 2 min | All pass |
| CI Pipeline | Unit + Integration | 10 min | 95% pass |
| Pre-release | Full suite + Performance | 30 min | All pass |
| Production | Smoke tests | 5 min | All pass |

---

## 6. Phase 5: Deployment

### 6.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Nginx      │────▶│  Streamlit   │────▶│   FastAPI    │        │
│  │   Proxy      │     │   :8501      │     │   :8000      │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│         │                    │                    │                 │
│         ▼                    ▼                    ▼                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   SSL/TLS    │     │   Redis      │     │  PostgreSQL  │        │
│  │   Certs      │     │   Cache      │     │   Database   │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Deployment Checklist

```markdown
## Pre-Deployment

- [ ] All tests passing (unit, integration, performance)
- [ ] Code review approved
- [ ] Documentation updated
- [ ] Security scan completed
- [ ] Dependencies audited

## Deployment Steps

- [ ] Create deployment branch
- [ ] Build Docker image
- [ ] Run smoke tests on staging
- [ ] Update changelog
- [ ] Deploy to production
- [ ] Verify health endpoints
- [ ] Monitor error rates (15 min)

## Post-Deployment

- [ ] Verify all endpoints accessible
- [ ] Check response times
- [ ] Confirm logging working
- [ ] Update status page
- [ ] Notify stakeholders
```

### 6.3 Rollback Plan

```bash
# In case of deployment failure:

# 1. Identify issue
kubectl logs -f deployment/streamlit-app

# 2. Rollback to previous version
kubectl rollout undo deployment/streamlit-app

# 3. Verify rollback
kubectl rollout status deployment/streamlit-app

# 4. Investigate issue
# - Check logs
# - Review recent changes
# - Create hotfix branch if needed
```

### 6.4 Feature Flags

```python
# config/feature_flags.py
FEATURE_FLAGS = {
    "api_explorer_enabled": True,
    "api_explorer_code_playground": True,
    "api_explorer_search": True,
    "api_explorer_history": True,
    "api_explorer_charts": True,
}

# Usage in code
if FEATURE_FLAGS.get("api_explorer_code_playground"):
    render_code_playground()
```

---

## 7. Phase 6: Maintenance

### 7.1 Monitoring & Alerting

#### Metrics to Track

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Page load time | > 3s | Warning |
| Search latency | > 200ms | Warning |
| Request error rate | > 5% | Critical |
| Code execution timeout | > 30s | Warning |

#### Dashboard Queries

```sql
-- Request success rate
SELECT 
    date_trunc('hour', timestamp) as hour,
    COUNT(*) FILTER (WHERE status_code < 400) * 100.0 / COUNT(*) as success_rate
FROM api_explorer_requests
GROUP BY 1
ORDER BY 1 DESC;

-- Most used endpoints
SELECT 
    endpoint_name,
    COUNT(*) as usage_count
FROM api_explorer_requests
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;

-- Average response times
SELECT 
    endpoint_name,
    AVG(response_time_ms) as avg_ms,
    p95(response_time_ms) as p95_ms
FROM api_explorer_requests
GROUP BY 1;
```

### 7.2 Maintenance Tasks

| Task | Frequency | Owner |
|------|-----------|-------|
| Update endpoint catalog | On API changes | Backend |
| Review error logs | Daily | DevOps |
| Performance optimization | Monthly | Engineering |
| Security patches | As needed | Security |
| Dependency updates | Quarterly | Engineering |

### 7.3 Support Procedures

#### Issue Triage

| Severity | Response Time | Examples |
|----------|---------------|----------|
| P0 - Critical | 15 min | Page not loading, security breach |
| P1 - High | 1 hour | Major feature broken |
| P2 - Medium | 4 hours | Minor feature broken |
| P3 - Low | 1 day | UI polish, enhancement |

#### Escalation Path

```
L1 Support → L2 Engineering → Tech Lead → Eng Manager
```

### 7.4 Documentation Maintenance

| Document | Update Trigger | Owner |
|----------|----------------|-------|
| User guide | Feature changes | Product |
| API catalog | Endpoint changes | Backend |
| This SDLC doc | Process changes | Engineering |
| Runbook | Incident learnings | DevOps |

---

## 8. Risk Assessment

### 8.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Code execution security | Medium | High | Sandbox, allowed-list, timeout |
| Search performance | Low | Medium | Indexing, caching |
| API unavailable | Medium | High | Health checks, error messages |
| Large response handling | Medium | Medium | Pagination, truncation |
| Browser compatibility | Low | Low | Testing, polyfills |

### 8.2 Security Considerations

#### Code Execution Sandbox

```python
# Blocked operations:
# - File system access (open, os.*)
# - Network (except requests to localhost)
# - System commands (subprocess, os.system)
# - Import of dangerous modules

BLOCKED_IMPORTS = [
    "os", "sys", "subprocess", "shutil",
    "socket", "http", "urllib",
    "pickle", "marshal", "ctypes",
    "__builtins__", "importlib"
]
```

#### Input Validation

```python
def validate_json_body(body_str: str) -> Tuple[bool, str]:
    """Validate JSON input before execution."""
    try:
        parsed = json.loads(body_str)
        if len(body_str) > 1_000_000:  # 1MB limit
            return False, "Request body too large"
        return True, parsed
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
```

---

## 9. Appendices

### 9.1 Glossary

| Term | Definition |
|------|------------|
| Endpoint | A specific URL path that accepts HTTP requests |
| Fuzzy Search | Search that matches similar but not exact terms |
| Code Playground | Interactive environment for running code |
| Sandbox | Restricted execution environment |

### 9.2 References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Postman Design Guidelines](https://www.postman.com/)
- [OWASP Security Guidelines](https://owasp.org/)

### 9.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-26 | Engineering | Initial document |

### 9.4 Approval Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| QA Lead | | | |
| Security | | | |

---

*End of Document*
