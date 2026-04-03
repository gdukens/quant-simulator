# On-Call Runbook - QuantLib Pro

## Table of Contents

- [Overview](#overview)
- [On-Call Schedule](#on-call-schedule)
- [Escalation Path](#escalation-path)
- [Common Issues](#common-issues)
- [Incident Response](#incident-response)
- [System Architecture](#system-architecture)
- [Tools & Access](#tools--access)
- [Playbooks](#playbooks)
- [Post-Incident](#post-incident)

---

## Overview

This runbook provides on-call engineers with procedures to diagnose and resolve production incidents for QuantLib Pro.

**On-Call Responsibilities:**
- Respond to alerts within 15 minutes
- Triage and resolve incidents
- Escalate when necessary
- Document all actions
- Participate in post-mortems

**Shift Duration:** 7 days (Monday 9am - Monday 9am)  
**Response SLA:** 15 minutes for P0/P1, 1 hour for P2/P3

---

## On-Call Schedule

### Current Rotation

| Week | Primary On-Call | Secondary On-Call | Manager On-Call |
|------|----------------|-------------------|-----------------|
| TBD | Engineer A | Engineer B | Manager X |
| TBD | Engineer B | Engineer C | Manager X |
| TBD | Engineer C | Engineer A | Manager Y |

**Schedule Tool:** PagerDuty (https://quantlib.pagerduty.com)  
**Handoff Time:** Mondays, 9:00 AM  
**Handoff Checklist:**
- [ ] Review open incidents
- [ ] Check system health dashboard
- [ ] Review planned maintenance
- [ ] Verify access to all systems
- [ ] Test alert routing

---

## Escalation Path

### Severity Levels

| Level | Description | Examples | Response Time | Escalation |
|-------|-------------|----------|---------------|------------|
| **P0** | Critical outage | Site down, data corruption | Immediate | Escalate after 30 min |
| **P1** | Major degradation | Key feature broken, high error rate | 15 minutes | Escalate after 1 hour |
| **P2** | Partial degradation | One feature impaired, slow response | 1 hour | Escalate after 4 hours |
| **P3** | Minor issue | Non-critical bug, cosmetic issue | 4 hours | No escalation needed |

### Escalation Contacts

**Level 1 - On-Call Engineer**
- Phone: (Set in PagerDuty)
- Slack: @oncall
- Handles: All incidents initially

**Level 2 - Tech Lead**
- Phone: +1-XXX-XXX-XXXX
- Slack: @tech-lead
- Escalate if: P0 unresolved in 30 min, P1 unresolved in 1 hour

**Level 3 - Engineering Manager**
- Phone: +1-XXX-XXX-XXXX
- Slack: @eng-manager
- Escalate if: Multi-hour outage, executive involvement needed

**Level 4 - CTO**
- Phone: +1-XXX-XXX-XXXX
- Escalate if: Company-threatening incident

### Domain Experts

| Area | Expert | Contact |
|------|--------|---------|
| Database | DBA Team | #dba-oncall |
| Security | Security Team | security@quantlib.com |
| Networking | NetOps | #netops |
| Data Pipeline | Data Engineering | #data-eng |
| Auth/IAM | Security Lead | TBD |

---

## Common Issues

### 1. Application Down / Not Responding

**Symptoms:**
- Health check failures
- 502/503 errors
- Timeout errors

**Diagnosis:**
```bash
# Check if application is running
docker ps | grep quantlib-app

# Check application logs
docker logs quantlib-app --tail 100

# Check resource usage
docker stats quantlib-app

# Check health endpoint
curl http://localhost:8501/_stcore/health
```

**Common Causes:**
- Out of memory (OOM kill)
- Unhandled exception
- Port conflicts
- Database connection failures

**Resolution:**
```bash
# Restart application
docker restart quantlib-app

# If restart fails, check logs
docker logs quantlib-app > /tmp/crash.log

# Full redeploy (last resort)
cd /opt/quantlib
docker-compose down && docker-compose up -d
```

**Escalate if:** Restart doesn't resolve within 30 minutes

---

### 2. High Error Rate (>2%)

**Symptoms:**
- Prometheus alert: `error_rate > 0.02`
- User reports of failures
- Grafana dashboard showing spike

**Diagnosis:**
```bash
# Check error logs
docker logs quantlib-app | grep ERROR | tail -50

# Check specific error types
docker logs quantlib-app | grep -oP 'ERROR: \K.*' | sort | uniq -c | sort -nr

# Check external API failures
curl http://localhost:8501/metrics | grep api_failure_total
```

**Common Causes:**
- External API outages (yfinance, Alpha Vantage)
- Database connection pool exhaustion
- Invalid user input not handled
- Calculation timeouts

**Resolution:**

**For external API issues:**
```bash
# Check API status
curl https://www.alphavantage.co/
curl https://cloud.iexapis.com/

# Force failover to backup provider
# Edit .env
sed -i 's/DEFAULT_DATA_PROVIDER=alpha_vantage/DEFAULT_DATA_PROVIDER=yfinance/' .env
docker restart quantlib-app
```

**For database issues:**
```bash
# Check connection pool
docker exec postgres psql -U quantlib -c "SELECT * FROM pg_stat_activity;"

# Restart database (CAUTION)
docker restart postgres
```

**Escalate if:** Error rate doesn't drop below 1% within 1 hour

---

### 3. Slow Response Times (P95 > 5s)

**Symptoms:**
- Prometheus alert: `http_request_duration_p95 > 5`
- User complaints about slowness
- Grafana showing high latency

**Diagnosis:**
```bash
# Check current response times
curl http://localhost:8501/metrics | grep http_request_duration

# Check slow queries
docker exec postgres psql -U quantlib -c "SELECT query, calls, mean_exec_time, max_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check Redis latency
docker exec redis redis-cli --latency

# Check CPU/memory
top -b -n 1 | head -20
```

**Common Causes:**
- Expensive calculation without caching
- Database query missing index
- Redis cache misses
- High concurrent user load

**Resolution:**

**Quick wins:**
```bash
# Clear Redis cache to force refresh
docker exec redis redis-cli FLUSHALL

# Restart application to clear memory
docker restart quantlib-app

# Scale horizontally (if using orchestration)
docker-compose scale quantlib-app=3
```

**Longer-term fixes:**
- Add database indexes (requires DBA)
- Optimize calculation algorithms
- Increase cache TTL
- Scale resources (more CPU/memory)

**Escalate if:** P95 doesn't drop below 3s within 2 hours

---

### 4. Database Connection Errors

**Symptoms:**
- Errors: `connection refused`, `connection timeout`, `too many connections`
- Application can't start
- Intermittent failures

**Diagnosis:**
```bash
# Check database is running
docker ps | grep postgres

# Check connection count
docker exec postgres psql -U quantlib -c "SELECT count(*) FROM pg_stat_activity;"

# Check max connections
docker exec postgres psql -U quantlib -c "SHOW max_connections;"

# Test connection
docker exec postgres psql -U quantlib -c "SELECT 1;"
```

**Resolution:**

**If too many connections:**
```bash
# Kill idle connections
docker exec postgres psql -U quantlib -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';"

# Increase max_connections (requires restart)
# Edit postgresql.conf
docker exec postgres bash -c "echo 'max_connections = 200' >> /var/lib/postgresql/data/postgresql.conf"
docker restart postgres
```

**If database is down:**
```bash
# Check logs
docker logs postgres --tail 100

# Restart database
docker restart postgres

# If corrupted, restore from backup
./scripts/restore.sh TIMESTAMP --database --from-s3
```

**Escalate if:** Database doesn't recover within 30 minutes

---

### 5. Redis Cache Failure

**Symptoms:**
- Errors: `connection refused` to Redis
- Slow response times (cache misses)
- Memory usage high

**Diagnosis:**
```bash
# Check Redis is running
docker ps | grep redis

# Check memory usage
docker exec redis redis-cli INFO memory

# Check eviction stats
docker exec redis redis-cli INFO stats | grep evicted

# Test connection
docker exec redis redis-cli PING
```

**Resolution:**

**If Redis is down:**
```bash
# Check logs
docker logs redis --tail 100

# Restart Redis
docker restart redis

# Verify it's back up
docker exec redis redis-cli PING
```

**If out of memory:**
```bash
# Clear cache (safe, data will re-populate)
docker exec redis redis-cli FLUSHALL

# Or selectively delete old keys
docker exec redis redis-cli --scan --pattern "cache:*" | xargs docker exec redis redis-cli DEL
```

**Escalate if:** Cache issues persist after restart

---

### 6. High Memory Usage (>90%)

**Symptoms:**
- Prometheus alert: `memory_usage > 0.9`
- OOM kills
- Application becoming unresponsive

**Diagnosis:**
```bash
# Check overall system memory
free -h

# Check container memory
docker stats --no-stream

# Check for memory leaks
docker exec quantlib-app ps aux --sort=-%mem | head

# Check Python memory usage
docker exec quantlib-app python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

**Resolution:**

**Immediate:**
```bash
# Restart application to clear memory
docker restart quantlib-app

# Scale resources (if using cloud)
# AWS
aws ecs update-service --service quantlib-pro-service --task-definition quantlib-pro-task-2GB

# GCP
gcloud run services update quantlib-pro --memory 4Gi
```

**Investigation:**
```python
# Add memory profiling to code
from memory_profiler import profile

@profile
def expensive_function():
    # Your code here
    pass
```

**Escalate if:** Memory usage doesn't stabilize below 75% after restart

---

### 7. Disk Space Full (>90%)

**Symptoms:**
- Prometheus alert: `disk_usage > 0.9`
- Errors: `No space left on device`
- Log rotation failures

**Diagnosis:**
```bash
# Check disk usage
df -h

# Find large files
du -sh /* | sort -hr | head -10

# Check log files
du -sh /var/log/*

# Check Docker volumes
docker system df
```

**Resolution:**

**Quick cleanup:**
```bash
# Clean up logs
find /var/log -name "*.log" -mtime +7 -delete

# Docker cleanup
docker system prune -a --volumes -f

# Remove old backups
find /backups -name "*.tar.gz" -mtime +30 -delete

# Compress logs
gzip /var/log/*.log
```

**Long-term:**
- Set up log rotation
- Increase disk size
- Move backups to cloud storage

**Escalate if:** Can't free up space or disk fills repeatedly

---

### 8. External API Failures

**Symptoms:**
- Errors: `API key invalid`, `rate limit exceeded`, `timeout`
- Data fetch failures
- Partial data displayed

**Diagnosis:**
```bash
# Check API status
curl https://www.alphavantage.co/
curl https://cloud.iexapis.com/v1/status

# Check API key
echo $ALPHA_VANTAGE_API_KEY

# Check rate limits
docker logs quantlib-app | grep "rate limit"
```

**Resolution:**

**For rate limiting:**
```bash
# Switch to backup provider
export DEFAULT_DATA_PROVIDER=yfinance
docker restart quantlib-app

# Or implement caching
export CACHE_TTL=86400  # 24 hours
docker restart quantlib-app
```

**For invalid API key:**
```bash
# Rotate API key (see secrets-management.md)
# Update secret in AWS/GCP/Azure
# Restart application to pick up new key
```

**Escalate if:** No data provider working

---

## Incident Response

### Step-by-Step Procedure

**1. Acknowledge Alert (Within 5 minutes)**
```bash
# In PagerDuty
- Click "Acknowledge"
- Note time

# In Slack
- Post in #incidents: "Acknowledged alert: <description>"
```

**2. Assess Severity (Within 10 minutes)**
- What's broken?
- How many users affected?
- Data integrity at risk?
- Classify as P0/P1/P2/P3

**3. Start Communication (Immediately)**
```
# Create incident channel
/incident create [title]

# Update status page
https://status.quantlib.com/admin
```

**4. Diagnose Issue (15-30 minutes)**
- Check dashboards
- Review logs
- Test systems
- Identify root cause

**5. Implement Fix**
- Apply resolution
- Monitor metrics
- Verify fix worked

**6. Verify Resolution**
- Check health checks
- Review metrics for 10 minutes
- Get user confirmation if possible

**7. Close Incident**
- Mark resolved in PagerDuty
- Update status page
- Post resolution in Slack

**8. Document**
- Write incident summary
- Schedule post-mortem (for P0/P1)

---

## System Architecture

### High-Level Overview

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │
┌──────▼───────────────────┐
│  Load Balancer (Nginx)   │
└──────┬───────────────────┘
       │
┌──────▼──────────────────┐
│  QuantLib App (Streamlit)│
└──┬────────┬──────────┬──┘
   │        │          │
┌──▼───┐ ┌─▼───┐  ┌───▼─────┐
│Redis │ │ DB  │  │  APIs   │
└──────┘ └─────┘  └─────────┘
```

### Key Components

| Component | Technology | Port | Purpose |
|-----------|-----------|------|---------|
| Application | Streamlit/Python | 8501 | Main app |
| Cache | Redis | 6379 | Session/data cache |
| Database | PostgreSQL | 5432 | Persistent data |
| Proxy | Nginx | 80/443 | Load balancing |
| Monitoring | Prometheus | 9090 | Metrics |
| Dashboards | Grafana | 3000 | Visualization |

### Data Flow

1. User request → Nginx
2. Nginx → Streamlit app
3. App checks Redis cache
4. If cache miss → Fetch from DB or external API
5. Store in cache
6. Return to user

---

## Tools & Access

### Required Access

Before your on-call shift, ensure you have:

- [ ] VPN access
- [ ] SSH keys for production servers
- [ ] AWS/GCP/Azure console access
- [ ] PagerDuty account
- [ ] Slack #incidents channel
- [ ] Grafana dashboards access
- [ ] Database credentials (from secrets manager)
- [ ] Runbook repository access

### Essential URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Production App | https://app.quantlib.com | Main application |
| Grafana | http://grafana.quantlib.com:3000 | Metrics dashboard |
| Prometheus | http://prometheus.quantlib.com:9090 | Metrics backend |
| Status Page | https://status.quantlib.com | Public status |
| PagerDuty | https://quantlib.pagerduty.com | Alerting |
| GitHub | https://github.com/gdukens/quant-simulator | Code repository |
| CI/CD | https://github.com/gdukens/quant-simulator/actions | Pipelines |

### Quick Commands

**Connect to production:**
```bash
# SSH
ssh admin@prod.quantlib.com

# Docker exec into app
docker exec -it quantlib-app bash

# Database connection
docker exec -it postgres psql -U quantlib -d quantlib_pro
```

**View logs:**
```bash
# Application logs (last 100 lines)
docker logs quantlib-app --tail 100 --follow

# Error logs only
docker logs quantlib-app 2>&1 | grep ERROR

# Database logs
docker logs postgres --tail 100

# Nginx access logs
docker logs nginx --tail 100
```

**Check metrics:**
```bash
# Application metrics
curl http://localhost:8501/metrics

# System metrics
docker stats

# Database stats
docker exec postgres psql -U quantlib -c "SELECT * FROM pg_stat_database WHERE datname = 'quantlib_pro';"
```

---

## Playbooks

### Playbook 1: Total Site Outage

**Severity:** P0  
**Goal:** Restore service within 30 minutes

**Steps:**
1. Acknowledge alert immediately
2. Post in #incidents: "Site down, investigating"
3. Update status page: "Major outage"
4. Check health endpoint:
   ```bash
   curl https://app.quantlib.com/_stcore/health
   ```
5. If no response, check infrastructure:
   ```bash
   # Is server up?
   ping prod.quantlib.com
   
   # Is nginx running?
   ssh admin@prod.quantlib.com "systemctl status nginx"
   
   # Is app running?
   ssh admin@prod.quantlib.com "docker ps | grep quantlib"
   ```
6. Restart services if needed:
   ```bash
   ssh admin@prod.quantlib.com "docker-compose restart"
   ```
7. If still down after 15 minutes, escalate to Tech Lead
8. If still down after 30 minutes, consider rollback:
   ```bash
   ./scripts/rollback.sh --phase full --reason "total-outage"
   ```

---

### Playbook 2: Database Emergency

**Severity:** P0/P1  
**Goal:** Restore database connectivity ASAP

**Steps:**
1. Check if database is responding:
   ```bash
   docker exec postgres psql -U quantlib -c "SELECT 1;"
   ```
2. If not responding, check logs:
   ```bash
   docker logs postgres --tail 200
   ```
3. Common issues:
   - **Too many connections:** Kill idle connections (see Common Issues #4)
   - **Corrupted data:** Restore from backup
   - **Out of disk:** Clean up space
4. If database won't start:
   ```bash
   # Check data directory
   docker exec postgres ls -la /var/lib/postgresql/data
   
   # Try safe mode
   docker exec postgres postgres --single -D /var/lib/postgresql/data
   ```
5. **Last resort:** Restore from backup:
   ```bash
   # Get latest backup
   ./scripts/restore.sh $(ls -t /backups/database_* | head -1 | grep -oP '\d{8}_\d{6}') --database
   ```
6. Escalate to DBA team if not resolved in 30 minutes

---

### Playbook 3: Data Corruption

**Severity:** P0  
**Goal:** Prevent further corruption, restore data integrity

**Steps:**
1. **DO NOT RESTART ANYTHING** (may lose evidence)
2. Take immediate snapshot:
   ```bash
   ./scripts/backup.sh --full
   ```
3. Stop application to prevent writes:
   ```bash
   docker stop quantlib-app
   ```
4. Assess damage:
   ```bash
   # Check database integrity
   docker exec postgres psql -U quantlib -c "VACUUM ANALYZE;"
   
   # Check for orphaned records
   # (specific to your schema)
   ```
5. Escalate immediately to Tech Lead + DBA
6. Update status page: "Data integrity issue, investigating"
7. Once fixed, run validation:
   ```bash
   # Run data validation tests
   pytest tests/data_integrity/
   ```

---

## Post-Incident

### Immediate (Within 1 hour of resolution)

- [ ] Mark incident as resolved in PagerDuty
- [ ] Update status page: "Resolved"
- [ ] Post resolution in #incidents Slack
- [ ] Create incident report document
- [ ] Tag incident with labels (severity, component, root cause)

### Short-term (Within 24 hours)

- [ ] Write incident summary (timeline, impact, resolution)
- [ ] Schedule post-mortem (for P0/P1)
- [ ] Identify action items
- [ ] Create follow-up tickets

### Long-term (Within 1 week)

- [ ] Conduct blameless post-mortem
- [ ] Update runbook with learnings
- [ ] Implement preventive measures
- [ ] Share learnings with team

### Incident Report Template

```markdown
# Incident Report: [Title]

**Incident ID:** INC-YYYY-NNNN  
**Severity:** PX  
**Date:** YYYY-MM-DD  
**Duration:** X hours Y minutes  
**Status:** Resolved

## Summary
[One-paragraph description of what happened]

## Timeline (all times UTC)
- HH:MM - Alert triggered
- HH:MM - Engineer acknowledged
- HH:MM - Root cause identified
- HH:MM - Fix applied
- HH:MM - Verified resolved

## Impact
- Users affected: X
- Revenue impact: $X
- Data integrity: OK/Compromised

## Root Cause
[Technical explanation of what caused the incident]

## Resolution
[What was done to fix it]

## Action Items
- [ ] Item 1 (Owner: X, Due: DATE)
- [ ] Item 2 (Owner: Y, Due: DATE)

## Lessons Learned
- What went well
- What could be improved
- How to prevent in future
```

---

## On-Call Best Practices

### Do's
 Acknowledge alerts within 15 minutes  
 Document everything in incident channel  
 Escalate early if unsure  
 Update status page proactively  
 Take breaks (get backup coverage)  
 Ask for help when needed  
 Keep calm under pressure  

### Don'ts
 Ignore alerts  
 Make changes without documenting  
 Skip communication steps  
 Work beyond exhaustion  
 Blame others  
 Rush without thinking  
 Forget to learn from incidents  

---

**Last Updated:** February 23, 2026  
**Owner:** DevOps Team  
**Feedback:** #oncall-feedback Slack channel
