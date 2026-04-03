# Monitoring and Alerting Configuration

Complete guide for configuring monitoring and alerting for QuantLib Pro production deployment.

## Table of Contents

- [Overview](#overview)
- [Monitoring Stack](#monitoring-stack)
- [Metrics Collection](#metrics-collection)
- [Alerting Rules](#alerting-rules)
- [Dashboard Configuration](#dashboard-configuration)
- [Alert Channels](#alert-channels)
- [SLOs and SLIs](#slos-and-slis)

---

## Overview

**Monitoring Philosophy:**
- Monitor what matters (user experience, business metrics, system health)
- Alert on symptoms, not causes
- Minimize alert fatigue (aim for 0 false positives)
- Make dashboards actionable

**Monitoring Layers:**
1. **Infrastructure** - CPU, memory, disk, network
2. **Application** - Request rate, latency, errors
3. **Business** - User activity, calculation success rate
4. **External** - API availability, third-party services

---

## Monitoring Stack

### Components

| Component | Purpose | Port | Version |
|-----------|---------|------|---------|
| Prometheus | Metrics collection & storage | 9090 | latest |
| Grafana | Visualization & dashboards | 3000 | latest |
| AlertManager | Alert routing & silencing | 9093 | latest |
| Node Exporter | System metrics | 9100 | latest |
| cAdvisor | Container metrics | 8080 | latest |
| Loki (optional) | Log aggregation | 3100 | latest |

### Installation

```bash
# Already included in docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d prometheus grafana alertmanager
```

### Configuration Files

```
monitoring/
├── prometheus.yml           # Prometheus config
├── alertmanager.yml        # AlertManager config
├── alerts/
│   ├── application.yml     # Application alerts
│   ├── infrastructure.yml  # Infra alerts
│   └── business.yml        # Business metric alerts
└── dashboards/
    ├── overview.json       # Main dashboard
    ├── application.json    # Application metrics
    └── infrastructure.json # Infrastructure metrics
```

---

## Metrics Collection

### Application Metrics

**Custom Metrics (exposed by QuantLib Pro):**

```python
# quantlib_pro/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'quantlib_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'quantlib_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
)

# Business metrics
portfolio_optimizations_total = Counter(
    'quantlib_portfolio_optimizations_total',
    'Total portfolio optimizations',
    ['method', 'status']
)

portfolio_optimization_duration_seconds = Histogram(
    'quantlib_portfolio_optimization_duration_seconds',
    'Portfolio optimization duration',
    ['method'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

monte_carlo_simulations_total = Counter(
    'quantlib_monte_carlo_simulations_total',
    'Total Monte Carlo simulations',
    ['num_simulations', 'status']
)

# Cache metrics
cache_hits_total = Counter(
    'quantlib_cache_hits_total',
    'Cache hit count'
)

cache_misses_total = Counter(
    'quantlib_cache_misses_total',
    'Cache miss count'
)

# Data fetch metrics
data_fetch_total = Counter(
    'quantlib_data_fetch_total',
    'Data fetch attempts',
    ['provider', 'status']
)

data_fetch_duration_seconds = Histogram(
    'quantlib_data_fetch_duration_seconds',
    'Data fetch duration',
    ['provider'],
    buckets=[0.5, 1, 2, 5, 10]
)

# Active users gauge
active_users = Gauge(
    'quantlib_active_users',
    'Number of active users'
)

# System health
health_check_status = Gauge(
    'quantlib_health_check_status',
    'Health check status (1=healthy, 0=unhealthy)',
    ['check_type']
)
```

### Infrastructure Metrics

**System (Node Exporter):**
- CPU usage: `node_cpu_seconds_total`
- Memory usage: `node_memory_MemAvailable_bytes`
- Disk usage: `node_filesystem_avail_bytes`
- Network I/O: `node_network_receive_bytes_total`

**Container (cAdvisor):**
- Container CPU: `container_cpu_usage_seconds_total`
- Container memory: `container_memory_usage_bytes`
- Container network: `container_network_receive_bytes_total`

**Database (PostgreSQL Exporter - optional):**
- Active connections: `pg_stat_database_numbackends`
- Transaction rate: `pg_stat_database_xact_commit`
- Query duration: `pg_stat_activity_max_tx_duration`

**Redis (Redis Exporter - optional):**
- Connected clients: `redis_connected_clients`
- Memory used: `redis_memory_used_bytes`
- Hit rate: `redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)`

---

## Alerting Rules

### Application Alerts

**File:** `monitoring/alerts/application.yml`

```yaml
groups:
  - name: application
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(quantlib_http_requests_total{status=~"5.."}[5m]))
            /
            sum(rate(quantlib_http_requests_total[5m]))
          ) > 0.02
        for: 5m
        labels:
          severity: critical
          component: application
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 2%)"
          runbook: "https://docs.quantlib.com/runbook#high-error-rate"
      
      # Slow response time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, 
            sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le)
          ) > 5
        for: 10m
        labels:
          severity: warning
          component: application
        annotations:
          summary: "Slow response times detected"
          description: "P95 latency is {{ $value }}s (threshold: 5s)"
          runbook: "https://docs.quantlib.com/runbook#slow-response"
      
      # Application down
      - alert: ApplicationDown
        expr: up{job="quantlib-app"} == 0
        for: 2m
        labels:
          severity: critical
          component: application
        annotations:
          summary: "QuantLib application is down"
          description: "Application has been down for more than 2 minutes"
          runbook: "https://docs.quantlib.com/runbook#app-down"
      
      # Health check failing
      - alert: HealthCheckFailing
        expr: quantlib_health_check_status{check_type="overall"} == 0
        for: 5m
        labels:
          severity: warning
          component: application
        annotations:
          summary: "Health check is failing"
          description: "Application health check has been failing for 5 minutes"
          runbook: "https://docs.quantlib.com/runbook#health-check"
      
      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: |
          (
            sum(rate(quantlib_cache_hits_total[10m]))
            /
            (sum(rate(quantlib_cache_hits_total[10m])) + sum(rate(quantlib_cache_misses_total[10m])))
          ) < 0.6
        for: 15m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 60%)"
          runbook: "https://docs.quantlib.com/runbook#low-cache-hit-rate"
      
      # External API failures
      - alert: ExternalAPIFailures
        expr: |
          (
            sum(rate(quantlib_data_fetch_total{status="error"}[5m]))
            /
            sum(rate(quantlib_data_fetch_total[5m]))
          ) > 0.1
        for: 10m
        labels:
          severity: warning
          component: data-fetching
        annotations:
          summary: "High external API failure rate"
          description: "{{ $value | humanizePercentage }} of API calls failing (threshold: 10%)"
          runbook: "https://docs.quantlib.com/runbook#api-failures"
```

### Infrastructure Alerts

**File:** `monitoring/alerts/infrastructure.yml`

```yaml
groups:
  - name: infrastructure
    interval: 30s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          (
            100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
          ) > 85
        for: 10m
        labels:
          severity: warning
          component: infrastructure
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}% (threshold: 85%)"
          runbook: "https://docs.quantlib.com/runbook#high-cpu"
      
      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
            /
            node_memory_MemTotal_bytes
          ) * 100 > 90
        for: 5m
        labels:
          severity: critical
          component: infrastructure
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}% (threshold: 90%)"
          runbook: "https://docs.quantlib.com/runbook#high-memory"
      
      # Low disk space
      - alert: LowDiskSpace
        expr: |
          (
            (node_filesystem_avail_bytes{mountpoint="/"}
            /
            node_filesystem_size_bytes{mountpoint="/"})
          ) * 100 < 15
        for: 5m
        labels:
          severity: warning
          component: infrastructure
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Only {{ $value }}% disk space remaining (threshold: 15%)"
          runbook: "https://docs.quantlib.com/runbook#low-disk"
      
      # Container down
      - alert: ContainerDown
        expr: |
          count(
            time() - container_last_seen{name=~"quantlib.*"} < 60
          ) by (name) == 0
        for: 2m
        labels:
          severity: critical
          component: container
        annotations:
          summary: "Container {{ $labels.name }} is down"
          description: "Container has been down for more than 2 minutes"
          runbook: "https://docs.quantlib.com/runbook#container-down"
      
      # Container restarting
      - alert: ContainerRestarting
        expr: rate(container_restart_count{name=~"quantlib.*"}[15m]) > 0
        for: 5m
        labels:
          severity: warning
          component: container
        annotations:
          summary: "Container {{ $labels.name }} is restarting"
          description: "Container has restarted {{ $value }} times in the last 15 minutes"
          runbook: "https://docs.quantlib.com/runbook#container-restart"
```

### Business Metrics Alerts

**File:** `monitoring/alerts/business.yml`

```yaml
groups:
  - name: business
    interval: 1m
    rules:
      # Low user activity
      - alert: LowUserActivity
        expr: quantlib_active_users < 5
        for: 30m
        labels:
          severity: info
          component: business
        annotations:
          summary: "Low user activity detected"
          description: "Only {{ $value }} active users (expected: >5 during business hours)"
      
      # High calculation failure rate
      - alert: HighCalculationFailureRate
        expr: |
          (
            sum(rate(quantlib_portfolio_optimizations_total{status="error"}[10m]))
            /
            sum(rate(quantlib_portfolio_optimizations_total[10m]))
          ) > 0.05
        for: 10m
        labels:
          severity: warning
          component: calculation
        annotations:
          summary: "High calculation failure rate"
          description: "{{ $value | humanizePercentage }} of calculations failing (threshold: 5%)"
          runbook: "https://docs.quantlib.com/runbook#calculation-failures"
```

---

## Dashboard Configuration

### Main Overview Dashboard

**Grafana JSON:** `monitoring/dashboards/overview.json`

**Panels:**

1. **System Health Indicator** (Gauge)
   - Query: `quantlib_health_check_status{check_type="overall"}`
   - Green: 1 (healthy), Red: 0 (unhealthy)

2. **Active Users** (Stat)
   - Query: `quantlib_active_users`

3. **Request Rate** (Graph)
   - Query: `sum(rate(quantlib_http_requests_total[5m]))`

4. **Error Rate** (Graph)
   - Query: 
     ```
     sum(rate(quantlib_http_requests_total{status=~"5.."}[5m]))
     /
     sum(rate(quantlib_http_requests_total[5m]))
     ```

5. **Response Time Percentiles** (Graph)
   - P50: `histogram_quantile(0.50, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))`
   - P95: `histogram_quantile(0.95, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))`
   - P99: `histogram_quantile(0.99, sum(rate(quantlib_http_request_duration_seconds_bucket[5m])) by (le))`

6. **CPU Usage** (Graph)
   - Query: `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`

7. **Memory Usage** (Graph)
   - Query: `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100`

8. **Disk Usage** (Graph)
   - Query: `(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100`

9. **Cache Hit Rate** (Gauge)
   - Query: 
     ```
     sum(rate(quantlib_cache_hits_total[5m]))
     /
     (sum(rate(quantlib_cache_hits_total[5m])) + sum(rate(quantlib_cache_misses_total[5m])))
     ```

10. **Top Endpoints by Request Count** (Table)
    - Query: `topk(10, sum(rate(quantlib_http_requests_total[5m])) by (endpoint))`

### Create Dashboards

```bash
# Import pre-configured dashboards
cd monitoring/dashboards

# Main overview
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @overview.json

# Application details
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @application.json

# Infrastructure
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @infrastructure.json
```

---

## Alert Channels

### AlertManager Configuration

**File:** `monitoring/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  
  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    
    # Warning alerts go to Slack
    - match:
        severity: warning
      receiver: 'slack-warnings'
    
    # Info alerts go to email
    - match:
        severity: info
      receiver: 'email'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          severity: '{{ .CommonLabels.severity }}'
          runbook: '{{ .CommonAnnotations.runbook }}'
  
  - name: 'slack-warnings'
    slack_configs:
      - channel: '#alerts-warnings'
        title: ' Warning: {{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
        color: 'warning'
  
  - name: 'email'
    email_configs:
      - to: 'ops@quantlib.com'
        from: 'alerts@quantlib.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@quantlib.com'
        auth_password: 'YOUR_EMAIL_PASSWORD'
        headers:
          Subject: 'QuantLib Alert: {{ .GroupLabels.alertname }}'

inhibit_rules:
  # Inhibit warning alerts if critical alert is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

### Slack Integration

```bash
# Create Slack webhook
# 1. Go to https://api.slack.com/apps
# 2. Create new app
# 3. Enable Incoming Webhooks
# 4. Create webhook for #alerts channel
# 5. Copy webhook URL to alertmanager.yml
```

### PagerDuty Integration

```bash
# Configure PagerDuty
# 1. Go to https://quantlib.pagerduty.com
# 2. Create service integration "Prometheus"
# 3. Copy integration key
# 4. Add to alertmanager.yml as service_key
```

### Email Alerts

```yaml
# For Gmail, enable "App Passwords"
# Settings > Security > 2-Step Verification > App passwords
# Use generated password in alertmanager.yml
```

---

## SLOs and SLIs

### Service Level Objectives

| Metric | SLO | Measurement Window | Consequences if Missed |
|--------|-----|-------------------|----------------------|
| **Availability** | 99.9% | 30 days | Refund 10% monthly fee |
| **Response Time (P95)** | < 2s | 7 days | Performance review |
| **Error Rate** | < 0.5% | 24 hours | Incident investigation |
| **Data Accuracy** | 100% | Always | Immediate fix required |

### Service Level Indicators

**Availability SLI:**
```promql
# Uptime percentage over 30 days
(
  sum(up{job="quantlib-app"} == 1)
  /
  count(up{job="quantlib-app"})
) * 100
```

**Response Time SLI:**
```promql
# P95 latency (target: < 2s)
histogram_quantile(0.95, 
  sum(rate(quantlib_http_request_duration_seconds_bucket[7d])) by (le)
)
```

**Error Rate SLI:**
```promql
# Error rate percentage (target: < 0.5%)
(
  sum(rate(quantlib_http_requests_total{status=~"5.."}[24h]))
  /
  sum(rate(quantlib_http_requests_total[24h]))
) * 100
```

### Error Budget

**Monthly Error Budget:**
- 99.9% uptime = 43.8 minutes of downtime allowed per month
- Track budget burn rate
- Alert if burning > 10% per week

```promql
# Error budget burn rate (target: < 10% per week)
(
  1 - (
    sum(up{job="quantlib-app"} == 1)
    /
    count(up{job="quantlib-app"})
  )
) / 0.001 * 100  # Show as % of error budget
```

---

## Testing Alerts

### Test Alert Firing

```bash
# Trigger test alert
curl -X POST http://localhost:9090/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert",
      "description": "Testing alert routing"
    }
  }'

# Verify alert in AlertManager
curl http://localhost:9093/api/v2/alerts

# Check Slack/email received
```

### Silence Alerts (Maintenance Window)

```bash
# Silence all alerts for 2 hours
curl -X POST http://localhost:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "alertname",
        "value": ".*",
        "isRegex": true
      }
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "endsAt": "'$(date -u -d '+2 hours' +%Y-%m-%dT%H:%M:%S.000Z)'",
    "createdBy": "oncall@quantlib.com",
    "comment": "Scheduled maintenance"
  }'
```

---

## Monitoring Checklist

### Daily
- [ ] Check Grafana main dashboard
- [ ] Review fired alerts from last 24h
- [ ] Verify all metrics collecting
- [ ] Check error budget burn rate

### Weekly
- [ ] Review SLO compliance
- [ ] Analyze slow query logs
- [ ] Check for metric anomalies
- [ ] Update alert thresholds if needed

### Monthly
- [ ] Review and tune alert rules
- [ ] Archive old metrics (>90 days)
- [ ] Update dashboards based on feedback
- [ ] Conduct chaos engineering test

---

**Last Updated:** February 23, 2026  
**Owner:** DevOps Team  
**Next Review:** After Week 22 completion
