# Performance Monitoring Dashboard

Grafana dashboard configuration for QuantLib Pro performance monitoring.

## Overview

This dashboard provides real-time visibility into:
- Application performance (latency, throughput, errors)
- System resources (CPU, memory, disk, network)
- Business metrics (users, calculations, cache efficiency)
- Database & cache performance
- External API health

## Dashboard Import

### Quick Setup

```bash
# Import dashboard into Grafana
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/dashboards/overview.json
```

---

## Dashboard Panels

### Row 1: System Health

#### Panel 1.1: Health Status (Gauge)
```json
{
  "title": "System Health",
  "type": "gauge",
  "targets": [
    {
      "expr": "quantlib_health_check_status{check_type=\"overall\"}"
    }
  ],
  "options": {
    "orientation": "horizontal",
    "thresholds": [
      { "value": 0, "color": "red" },
      { "value": 1, "color": "green" }
    ]
  }
}
```

#### Panel 1.2: Active Users (Stat)
```json
{
  "title": "Active Users",
  "type": "stat",
  "targets": [
    {
      "expr": "quantlib_active_users"
    }
  ],
  "options": {
    "colorMode": "value",
    "graphMode": "area",
    "orientation": "horizontal"
  }
}
```

#### Panel 1.3: Request Rate (Stat with Sparkline)
```json
{
  "title": "Request Rate",
  "type": "stat",
  "targets": [
    {
      "expr": "sum(rate(quantlib_http_requests_total[5m]))",
      "legendFormat": "req/s"
    }
  ],
  "options": {
    "colorMode": "value",
    "graphMode": "area"
  }
}
```

#### Panel 1.4: Error Rate (Gauge)
```json
{
  "title": "Error Rate",
  "type": "gauge",
  "targets": [
    {
      "expr": "sum(rate(quantlib_http_requests_total{status=~\"5..\"}[5m])) / sum(rate(quantlib_http_requests_total[5m])) * 100"
    }
  ],
  "options": {
    "unit": "percent",
    "thresholds": [
      { "value": 0, "color": "green" },
      { "value": 0.5, "color": "yellow" },
      { "value": 2, "color": "red" }
    ]
  }
}
```

---

### Row 2: Application Performance

#### Panel 2.1: Response Time Percentiles (Graph)
```json
{
  "title": "Response Time Percentiles",
  "type": "graph",
  "targets": [
    {
      "expr": "histogram_quantile(0.50, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))",
      "legendFormat": "P50"
    },
    {
      "expr": "histogram_quantile(0.95, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))",
      "legendFormat": "P95"
    },
    {
      "expr": "histogram_quantile(0.99, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))",
      "legendFormat": "P99"
    }
  ],
  "yAxes": [
    {
      "format": "s",
      "label": "Latency"
    }
  ],
  "alert": {
    "conditions": [
      {
        "evaluator": {
          "params": [5],
          "type": "gt"
        },
        "operator": {
          "type": "and"
        },
        "query": {
          "params": ["P95", "5m", "now"]
        },
        "reducer": {
          "params": [],
          "type": "avg"
        },
        "type": "query"
      }
    ],
    "frequency": "1m",
    "handler": 1,
    "name": "High P95 Latency",
    "message": "P95 latency exceeded 5 seconds"
  }
}
```

#### Panel 2.2: Request Rate by Endpoint (Graph)
```json
{
  "title": "Request Rate by Endpoint",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(quantlib_http_requests_total[5m])) by (endpoint)",
      "legendFormat": "{{ endpoint }}"
    }
  ],
  "yAxes": [
    {
      "format": "ops",
      "label": "Requests/sec"
    }
  ]
}
```

#### Panel 2.3: Top Slow Endpoints (Table)
```json
{
  "title": "Top 10 Slow Endpoints",
  "type": "table",
  "targets": [
    {
      "expr": "topk(10, histogram_quantile(0.95, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (endpoint, le)))",
      "format": "table",
      "instant": true
    }
  ],
  "transformations": [
    {
      "id": "organize",
      "options": {
        "excludeByName": {},
        "indexByName": {},
        "renameByName": {
          "endpoint": "Endpoint",
          "Value": "P95 Latency (s)"
        }
      }
    }
  ]
}
```

---

### Row 3: Business Metrics

#### Panel 3.1: Portfolio Optimizations (Graph)
```json
{
  "title": "Portfolio Optimizations",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(quantlib_portfolio_optimizations_total{status=\"success\"}[5m]))",
      "legendFormat": "Success"
    },
    {
      "expr": "sum(rate(quantlib_portfolio_optimizations_total{status=\"error\"}[5m]))",
      "legendFormat": "Failed"
    }
  ],
  "yAxes": [
    {
      "format": "ops",
      "label": "Operations/sec"
    }
  ]
}
```

#### Panel 3.2: Optimization Duration (Heatmap)
```json
{
  "title": "Portfolio Optimization Duration",
  "type": "heatmap",
  "targets": [
    {
      "expr": "sum(rate(quantlib_portfolio_optimization_duration_seconds_bucket[5m])) by (le)",
      "format": "heatmap",
      "legendFormat": "{{ le }}"
    }
  ],
  "yAxis": {
    "format": "s",
    "label": "Duration"
  }
}
```

#### Panel 3.3: Monte Carlo Simulations (Graph)
```json
{
  "title": "Monte Carlo Simulations",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(quantlib_monte_carlo_simulations_total{status=\"success\"}[5m])) by (num_simulations)",
      "legendFormat": "{{ num_simulations }} simulations"
    }
  ],
  "yAxes": [
    {
      "format": "ops",
      "label": "Simulations/sec"
    }
  ]
}
```

#### Panel 3.4: Calculation Success Rate (Gauge)
```json
{
  "title": "Calculation Success Rate",
  "type": "gauge",
  "targets": [
    {
      "expr": "sum(rate(quantlib_portfolio_optimizations_total{status=\"success\"}[5m])) / sum(rate(quantlib_portfolio_optimizations_total[5m])) * 100"
    }
  ],
  "options": {
    "unit": "percent",
    "thresholds": [
      { "value": 0, "color": "red" },
      { "value": 95, "color": "yellow" },
      { "value": 99, "color": "green" }
    ]
  }
}
```

---

### Row 4: Cache Performance

#### Panel 4.1: Cache Hit Rate (Graph)
```json
{
  "title": "Cache Hit Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(quantlib_cache_hits_total[5m])) / (sum(rate(quantlib_cache_hits_total[5m])) + sum(rate(quantlib_cache_misses_total[5m]))) * 100",
      "legendFormat": "Hit Rate %"
    }
  ],
  "yAxes": [
    {
      "format": "percent",
      "min": 0,
      "max": 100
    }
  ],
  "thresholds": [
    {
      "value": 60,
      "colorMode": "critical",
      "op": "lt",
      "fill": true,
      "line": true
    }
  ]
}
```

#### Panel 4.2: Cache Operations (Graph)
```json
{
  "title": "Cache Operations",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(quantlib_cache_hits_total[5m]))",
      "legendFormat": "Hits"
    },
    {
      "expr": "sum(rate(quantlib_cache_misses_total[5m]))",
      "legendFormat": "Misses"
    }
  ],
  "yAxes": [
    {
      "format": "ops",
      "label": "Operations/sec"
    }
  ]
}
```

---

### Row 5: External Dependencies

#### Panel 5.1: Data Provider Success Rate (Graph)
```json
{
  "title": "Data Provider Success Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "sum(rate(quantlib_data_fetch_total{status=\"success\"}[5m])) by (provider) / sum(rate(quantlib_data_fetch_total[5m])) by (provider) * 100",
      "legendFormat": "{{ provider }}"
    }
  ],
  "yAxes": [
    {
      "format": "percent",
      "min": 0,
      "max": 100
    }
  ]
}
```

#### Panel 5.2: Data Fetch Duration by Provider (Graph)
```json
{
  "title": "Data Fetch Duration by Provider",
  "type": "graph",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, sum(rate(quantlib_data_fetch_duration_seconds_bucket[5m])) by (provider, le))",
      "legendFormat": "{{ provider }} P95"
    }
  ],
  "yAxes": [
    {
      "format": "s",
      "label": "Duration"
    }
  ]
}
```

---

### Row 6: System Resources

#### Panel 6.1: CPU Usage (Graph)
```json
{
  "title": "CPU Usage",
  "type": "graph",
  "targets": [
    {
      "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
      "legendFormat": "CPU %"
    }
  ],
  "yAxes": [
    {
      "format": "percent",
      "min": 0,
      "max": 100
    }
  ],
  "thresholds": [
    {
      "value": 85,
      "colorMode": "critical",
      "op": "gt",
      "fill": true,
      "line": true
    }
  ]
}
```

#### Panel 6.2: Memory Usage (Graph)
```json
{
  "title": "Memory Usage",
  "type": "graph",
  "targets": [
    {
      "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
      "legendFormat": "Memory %"
    }
  ],
  "yAxes": [
    {
      "format": "percent",
      "min": 0,
      "max": 100
    }
  ],
  "thresholds": [
    {
      "value": 90,
      "colorMode": "critical",
      "op": "gt",
      "fill": true,
      "line": true
    }
  ]
}
```

#### Panel 6.3: Disk Usage (Gauge)
```json
{
  "title": "Disk Usage",
  "type": "gauge",
  "targets": [
    {
      "expr": "(node_filesystem_size_bytes{mountpoint=\"/\"} - node_filesystem_avail_bytes{mountpoint=\"/\"}) / node_filesystem_size_bytes{mountpoint=\"/\"} * 100"
    }
  ],
  "options": {
    "unit": "percent",
    "thresholds": [
      { "value": 0, "color": "green" },
      { "value": 75, "color": "yellow" },
      { "value": 90, "color": "red" }
    ]
  }
}
```

#### Panel 6.4: Network I/O (Graph)
```json
{
  "title": "Network I/O",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(node_network_receive_bytes_total{device!=\"lo\"}[5m])",
      "legendFormat": "Receive"
    },
    {
      "expr": "rate(node_network_transmit_bytes_total{device!=\"lo\"}[5m])",
      "legendFormat": "Transmit"
    }
  ],
  "yAxes": [
    {
      "format": "Bps",
      "label": "Bytes/sec"
    }
  ]
}
```

---

### Row 7: Database Performance

#### Panel 7.1: Active Database Connections (Graph)
```json
{
  "title": "Active Database Connections",
  "type": "graph",
  "targets": [
    {
      "expr": "pg_stat_database_numbackends{datname=\"quantlib\"}"
    }
  ],
  "yAxes": [
    {
      "format": "short",
      "label": "Connections"
    }
  ],
  "thresholds": [
    {
      "value": 80,
      "colorMode": "critical",
      "op": "gt"
    }
  ]
}
```

#### Panel 7.2: Transaction Rate (Graph)
```json
{
  "title": "Database Transaction Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(pg_stat_database_xact_commit{datname=\"quantlib\"}[5m])",
      "legendFormat": "Commits"
    },
    {
      "expr": "rate(pg_stat_database_xact_rollback{datname=\"quantlib\"}[5m])",
      "legendFormat": "Rollbacks"
    }
  ],
  "yAxes": [
    {
      "format": "ops",
      "label": "Transactions/sec"
    }
  ]
}
```

---

## Complete Dashboard JSON

### File: `monitoring/dashboards/overview.json`

```json
{
  "dashboard": {
    "id": null,
    "uid": "quantlib-overview",
    "title": "QuantLib Pro - Overview",
    "tags": ["quantlib", "production"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "30s",
    
    "panels": [
      {
        "id": 1,
        "gridPos": { "h": 4, "w": 6, "x": 0, "y": 0 },
        "type": "gauge",
        "title": "System Health",
        "targets": [
          {
            "expr": "quantlib_health_check_status{check_type=\"overall\"}",
            "refId": "A"
          }
        ],
        "options": {
          "orientation": "horizontal",
          "showThresholdLabels": false,
          "showThresholdMarkers": true
        },
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": 0, "color": "red" },
                { "value": 1, "color": "green" }
              ]
            },
            "min": 0,
            "max": 1
          }
        }
      },
      
      {
        "id": 2,
        "gridPos": { "h": 4, "w": 6, "x": 6, "y": 0 },
        "type": "stat",
        "title": "Active Users",
        "targets": [
          {
            "expr": "quantlib_active_users",
            "refId": "A"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "horizontal"
        }
      },
      
      {
        "id": 3,
        "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
        "type": "stat",
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(quantlib_http_requests_total[5m]))",
            "refId": "A"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area"
        },
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      
      {
        "id": 4,
        "gridPos": { "h": 4, "w": 6, "x": 18, "y": 0 },
        "type": "gauge",
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(quantlib_http_requests_total{status=~\"5..\"}[5m])) / sum(rate(quantlib_http_requests_total[5m])) * 100",
            "refId": "A"
          }
        ],
        "options": {
          "orientation": "horizontal",
          "reduceOptions": {
            "values": false,
            "fields": "",
            "calcs": ["lastNotNull"]
          }
        },
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 0.5, "color": "yellow" },
                { "value": 2, "color": "red" }
              ]
            },
            "unit": "percent",
            "min": 0,
            "max": 5
          }
        }
      },
      
      {
        "id": 5,
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
        "type": "graph",
        "title": "Response Time Percentiles",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P50",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P99",
            "refId": "C"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "Latency"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [5],
                "type": "gt"
              },
              "query": {
                "params": ["B", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "1m",
          "handler": 1,
          "name": "High P95 Latency",
          "message": "P95 latency exceeded 5 seconds",
          "noDataState": "no_data"
        }
      },
      
      {
        "id": 6,
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
        "type": "graph",
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "sum(rate(quantlib_cache_hits_total[5m])) / (sum(rate(quantlib_cache_hits_total[5m])) + sum(rate(quantlib_cache_misses_total[5m]))) * 100",
            "legendFormat": "Hit Rate %",
            "refId": "A"
          }
        ],
        "yaxes": [
          {
            "format": "percent",
            "min": 0,
            "max": 100
          }
        ]
      }
    ]
  },
  
  "overwrite": true
}
```

---

## Custom Dashboards

### Application-Specific Dashboard

Create separate dashboards for:
1. **Portfolio Module** - Portfolio optimizations, risk calculations
2. **Monte Carlo Module** - Simulation performance, convergence
3. **Market Data Module** - Data fetch performance, provider health
4. **User Analytics** - User activity, feature usage

### Infrastructure Dashboard

Focus on:
- Container health (Docker stats)
- Database performance (PostgreSQL metrics)
- Cache performance (Redis metrics)
- Network traffic

---

## Dashboard Variables

Add template variables for filtering:

```json
"templating": {
  "list": [
    {
      "name": "datasource",
      "type": "datasource",
      "query": "prometheus"
    },
    {
      "name": "environment",
      "type": "query",
      "query": "label_values(quantlib_http_requests_total, environment)",
      "multi": false,
      "includeAll": false
    },
    {
      "name": "endpoint",
      "type": "query",
      "query": "label_values(quantlib_http_requests_total, endpoint)",
      "multi": true,
      "includeAll": true
    }
  ]
}
```

---

## Alert Configuration

Dashboards can include embedded alerts that trigger notifications:

```json
"alert": {
  "conditions": [
    {
      "evaluator": {
        "params": [5],
        "type": "gt"
      },
      "operator": {
        "type": "and"
      },
      "query": {
        "params": ["A", "5m", "now"]
      },
      "reducer": {
        "params": [],
        "type": "avg"
      },
      "type": "query"
    }
  ],
  "executionErrorState": "alerting",
  "frequency": "1m",
  "handler": 1,
  "name": "Dashboard Alert",
  "message": "Metric exceeded threshold",
  "noDataState": "no_data",
  "notifications": [
    {"uid": "slack-notification"}
  ]
}
```

---

## Dashboard Management

### Export Dashboard

```bash
# Export dashboard from Grafana
curl http://admin:admin@localhost:3000/api/dashboards/uid/quantlib-overview \
  | jq '.dashboard' > monitoring/dashboards/overview-backup.json
```

### Version Control

```bash
# Commit dashboard to Git
git add monitoring/dashboards/
git commit -m "Update Grafana dashboards"
git push
```

### Automated Import on Deployment

Add to deployment script:

```bash
# deploy/import-grafana-dashboards.sh
#!/bin/bash

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

for dashboard in monitoring/dashboards/*.json; do
  echo "Importing $dashboard..."
  curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
    -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
    -H "Content-Type: application/json" \
    -d @"$dashboard"
done

echo "All dashboards imported successfully!"
```

---

**Last Updated:** February 23, 2026  
**Owner:** DevOps Team  
**Next Review:** After Week 22 completion
