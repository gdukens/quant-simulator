# Load Testing Guide

Comprehensive guide for load testing QuantLib Pro in production environments.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Test Scenarios](#test-scenarios)
- [Performance Targets](#performance-targets)
- [Running Tests](#running-tests)
- [Analyzing Results](#analyzing-results)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

Load testing validates that QuantLib Pro can handle expected traffic and identifies performance bottlenecks before production deployment.

**Tools:**
- **Locust** - Python-based load testing framework
- **Apache Bench (ab)** - Quick HTTP benchmarking
- **k6** - Modern load testing (optional)

**Key Metrics:**
- Response time (P50, P95, P99)
- Requests per second (RPS)
- Error rate (%)
- Resource utilization (CPU, memory, disk)
- Concurrent users

## Installation

### Locust

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

### Apache Bench (Optional)

```bash
# Ubuntu/Debian
sudo apt-get install apache2-utils

# macOS
brew install apache-bench

# Windows (included with Apache)
choco install apache-httpd
```

### k6 (Optional)

```bash
# Ubuntu/Debian
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# macOS
brew install k6
```

## Quick Start

### Basic Load Test

```bash
# Start application
docker-compose -f docker-compose.prod.yml up -d

# Run basic load test (50 users, 5 minutes)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 5m \
    --headless
```

### Web UI Mode

```bash
# Start Locust web interface
locust -f tests/load/locustfile.py --host=http://localhost:8501

# Open browser: http://localhost:8089
# Configure users and spawn rate
# Click "Start swarming"
```

## Test Scenarios

### 1. Baseline Test

**Purpose:** Establish baseline performance metrics

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 10 \
    --spawn-rate 2 \
    --run-time 3m \
    --headless
```

**Expected Results:**
- P95 response time: < 2s
- Error rate: 0%
- RPS: 20-30

### 2. Normal Load Test

**Purpose:** Simulate typical production traffic

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 10m \
    --headless \
    --html report_normal.html
```

**Expected Results:**
- P95 response time: < 3s
- Error rate: < 1%
- RPS: 80-100

### 3. Peak Load Test

**Purpose:** Test capacity during peak hours

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 15m \
    --headless \
    --html report_peak.html
```

**Expected Results:**
- P95 response time: < 5s
- Error rate: < 2%
- RPS: 150-200

### 4. Stress Test

**Purpose:** Find breaking point

```bash
# Gradually increase users until failure
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 500 \
    --spawn-rate 25 \
    --run-time 20m \
    --headless \
    --html report_stress.html
```

**Look for:**
- When does error rate exceed 5%?
- At what user count do response times degrade?
- What resource hits 100% first?

### 5. Spike Test

**Purpose:** Test rapid traffic increases

```bash
# Use SpikeLoadShape from locustfile.py
# Modify locustfile.py to use SpikeLoadShape class

locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --headless \
    --html report_spike.html
```

**Expected Results:**
- System should handle spike without crashes
- Recovery time: < 30s after spike
- No memory leaks

### 6. Endurance Test

**Purpose:** Identify memory leaks and stability issues

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 30 \
    --spawn-rate 3 \
    --run-time 2h \
    --headless \
    --html report_endurance.html
```

**Monitor:**
- Memory usage over time (should be stable)
- Connection pool exhaustion
- Disk space (logs)

## Performance Targets

### Response Times

| Endpoint | P50 | P95 | P99 | Max |
|----------|-----|-----|-----|-----|
| Health checks | < 50ms | < 100ms | < 200ms | < 500ms |
| Homepage | < 500ms | < 1s | < 2s | < 5s |
| Portfolio optimization | < 2s | < 5s | < 10s | < 30s |
| Monte Carlo (1k sims) | < 3s | < 8s | < 15s | < 60s |
| Backtesting (1yr) | < 5s | < 15s | < 30s | < 120s |

### Throughput

| Scenario | Users | Target RPS | Min RPS |
|----------|-------|------------|---------|
| Baseline | 10 | 20 | 15 |
| Normal | 50 | 100 | 80 |
| Peak | 100 | 200 | 150 |

### Error Rates

- Normal load: < 1%
- Peak load: < 2%
- Stress test: < 5% (when below breaking point)

### Resource Utilization

- CPU: < 80% average (< 95% peak)
- Memory: < 75% average (< 90% peak)
- Disk: < 80% capacity

## Running Tests

### Local Testing

```bash
# 1. Start application with monitoring
docker-compose -f docker-compose.prod.yml up -d

# 2. Verify health
curl http://localhost:8501/_stcore/health

# 3. Run load test
locust -f tests/load/locustfile.py \
    --host=http://localhost:8501 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 10m \
    --headless \
    --html reports/loadtest_$(date +%Y%m%d_%H%M%S).html

# 4. Monitor resources
docker stats quantlib-app
```

### Cloud Testing

#### Test from AWS EC2

```bash
# Launch EC2 instance (t3.large recommended)
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.large \
    --key-name your-key

# SSH into instance
ssh -i your-key.pem ubuntu@<EC2_IP>

# Install dependencies
sudo apt-get update
sudo apt-get install python3-pip
pip3 install locust

# Clone repo and run tests
git clone https://github.com/gdukens/quant-simulator.git
cd quant-simulator
locust -f tests/load/locustfile.py \
    --host=https://your-production-url.com \
    --users 100 \
    --spawn-rate 10 \
    --run-time 15m \
    --headless
```

#### Distributed Load Testing

```bash
# Master node
locust -f tests/load/locustfile.py \
    --host=http://your-app.com \
    --master

# Worker nodes (run on multiple machines)
locust -f tests/load/locustfile.py \
    --host=http://your-app.com \
    --worker \
    --master-host=<MASTER_IP>
```

### Apache Bench (Quick Tests)

```bash
# Simple benchmark (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8501/

# With keep-alive
ab -n 1000 -c 50 -k http://localhost:8501/

# POST request
ab -n 100 -c 10 -p data.json -T application/json http://localhost:8501/api/optimize
```

## Analyzing Results

### Locust HTML Reports

Reports include:
- Total requests by endpoint
- Response time distribution (P50, P95, P99)
- Failures and error rates
- RPS over time
- Number of users over time

**Key sections to review:**
1. **Statistics** - Overall performance metrics
2. **Charts** - Response time and RPS trends
3. **Failures** - Error details and patterns
4. **Exceptions** - Stack traces

### Command-line Output

```
[2024-01-15 14:30:00] Name                      # reqs      # fails |    Avg     Min     Max  Median
[2024-01-15 14:30:00] ----------------------------------------------------------------
[2024-01-15 14:30:00] GET /health                 1200     0 (0%)  |     45      20     150      40
[2024-01-15 14:30:00] GET /                        850     5 (0.6%)|    680     200    3500     550
[2024-01-15 14:30:00] POST /api/optimize           120     2 (1.7%)|   2400     800   15000    2100
[2024-01-15 14:30:00] ----------------------------------------------------------------
[2024-01-15 14:30:00] Aggregated                  2170     7 (0.3%)|    589      20   15000     400
```

**What to look for:**
- **High failure rate** → Application errors or timeouts
- **Increasing response times** → Resource exhaustion
- **Timeouts** → Insufficient workers or slow queries

### Monitoring Dashboards

**Prometheus + Grafana:**
```bash
# Open Grafana
open http://localhost:3000

# Check dashboards:
# - System metrics (CPU, memory, disk)
# - Application metrics (request rate, errors)
# - Database metrics (query time, connections)
```

**Key metrics during load test:**
- CPU utilization trend
- Memory growth (check for leaks)
- Response time P95/P99
- Error rate
- Active connections

### Docker Stats

```bash
# Monitor container resources during test
docker stats quantlib-app

# Output:
# CONTAINER ID   NAME            CPU %   MEM USAGE / LIMIT   MEM %   NET I/O
# abc123         quantlib-app    75%     1.5GiB / 4GiB      37.5%   1.2GB / 850MB
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/load-test.yml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Locust
        run: pip install locust
      
      - name: Run load test
        run: |
          locust -f tests/load/locustfile.py \
            --host=${{ secrets.STAGING_URL }} \
            --users 50 \
            --spawn-rate 5 \
            --run-time 5m \
            --headless \
            --html loadtest-report.html
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: loadtest-report
          path: loadtest-report.html
      
      - name: Fail if error rate > 2%
        run: |
          ERROR_RATE=$(grep "Total Fails" loadtest-report.html | grep -oP '\d+\.\d+')
          if (( $(echo "$ERROR_RATE > 2.0" | bc -l) )); then
            echo "Error rate too high: $ERROR_RATE%"
            exit 1
          fi
```

## Troubleshooting

### High Error Rates

**Problem:** Error rate > 5%

**Diagnosis:**
```bash
# Check application logs
docker logs quantlib-app | grep ERROR

# Check health endpoint
curl http://localhost:8501/health
```

**Solutions:**
- Increase resources (CPU, memory)
- Optimize database queries
- Enable caching
- Increase worker count

### Slow Response Times

**Problem:** P95 response time > 10s

**Diagnosis:**
```bash
# Check slow queries
# Check Redis cache hit rate
docker exec -it redis redis-cli INFO stats | grep hit_rate

# Profile application
# Add profiling to code (see production-deployment.md)
```

**Solutions:**
- Add database indexes
- Increase cache TTL
- Optimize algorithms
- Use async processing for heavy tasks

### Memory Leaks

**Problem:** Memory usage increases over time

**Diagnosis:**
```bash
# Monitor memory during endurance test
docker stats --format "table {{.Container}}\t{{.MemUsage}}"

# Check for memory leaks in code
# Use memory profilers (memory_profiler, tracemalloc)
```

**Solutions:**
- Fix unclosed connections
- Clear caches periodically
- Use generators instead of lists
- Profile and optimize

### Connection Timeouts

**Problem:** Many connection timeout errors

**Diagnosis:**
```bash
# Check connection pool
# Check database max connections
docker exec -it postgres psql -U quantlib -c "SHOW max_connections;"
```

**Solutions:**
- Increase connection pool size
- Increase database max connections
- Add connection retry logic
- Use connection pooling

### Rate Limiting

**Problem:** 429 Too Many Requests errors

**Diagnosis:**
```bash
# Check if rate limiting is enabled
grep RATE_LIMIT .env
```

**Solutions:**
- Adjust rate limits for production
- Implement backoff strategy
- Use queue for heavy workloads

## Best Practices

### Before Testing

- [ ] Test in staging environment first
- [ ] Notify team of load test schedule
- [ ] Set up monitoring dashboards
- [ ] Create baseline performance metrics
- [ ] Have rollback plan ready

### During Testing

- [ ] Monitor real-time metrics
- [ ] Watch for error spikes
- [ ] Check resource utilization
- [ ] Document any anomalies
- [ ] Be ready to abort if issues arise

### After Testing

- [ ] Analyze results thoroughly
- [ ] Compare with performance targets
- [ ] Identify bottlenecks
- [ ] Create action items for improvements
- [ ] Update documentation

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [Apache Bench Guide](https://httpd.apache.org/docs/2.4/programs/ab.html)
- [k6 Documentation](https://k6.io/docs/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/performance-testing.html)

---

**Remember:** Load testing should be done regularly (weekly/monthly) to catch performance regressions early!
