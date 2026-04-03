# Phased Rollout Plan - QuantLib Pro Production Deployment

## Overview

This document outlines the phased rollout strategy for QuantLib Pro production deployment, minimizing risk through gradual user exposure.

**Strategy:** Progressive rollout with health monitoring at each stage  
**Timeline:** 7-14 days depending on metrics  
**Rollback Trigger:** Error rate > 2% or P95 latency > 5s

---

## Rollout Phases

### Phase 0: Pre-Production (Days -7 to -1)

**Target:** Final validation before production release

**Activities:**
- [ ] Complete all Week 19-20 deployment tasks
- [ ] Run full security audit (penetration testing)
- [ ] Execute load testing (stress test, endurance test)
- [ ] Verify all monitoring dashboards operational
- [ ] Test rollback procedures
- [ ] Conduct disaster recovery drill
- [ ] Train on-call team
- [ ] Prepare communication plan

**Go/No-Go Criteria:**
-  All critical bugs resolved
-  Load testing meets performance targets
-  Security scan shows no critical vulnerabilities
-  Backup/restore procedures tested
-  Monitoring alerts configured
-  Rollback plan validated
-  On-call rotation established

**Sign-off Required:** Tech Lead, Security Lead, Product Owner

---

### Phase 1: Canary Deployment (5% of Traffic)

**Duration:** 24-48 hours  
**Target Users:** 5% of production traffic (canary group)  
**Monitoring Interval:** Every 15 minutes

#### Implementation

**Traffic Split:**
```yaml
# Nginx/Load Balancer Configuration
upstream production {
    server prod-v1.quantlib.com weight=95;  # Existing stable version
    server prod-v2.quantlib.com weight=5;   # New version (canary)
}
```

**Feature Flag:**
```python
# Gradual rollout using feature flags
CANARY_USERS = ["user1@example.com", "user2@example.com"]  # Beta testers
CANARY_PERCENTAGE = 5

def is_canary_user(user_email):
    return (
        user_email in CANARY_USERS or
        hash(user_email) % 100 < CANARY_PERCENTAGE
    )
```

#### Success Metrics

| Metric | Target | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Error Rate | < 0.5% | > 1% | > 2% |
| P95 Latency | < 2s | > 3s | > 5s |
| P99 Latency | < 5s | > 8s | > 10s |
| Availability | > 99.9% | < 99.5% | < 99% |
| Memory Usage | < 60% | > 75% | > 90% |
| CPU Usage | < 50% | > 70% | > 85% |

#### Monitoring Checklist

Every 15 minutes, check:
- [ ] Error rate dashboard (Grafana)
- [ ] Response time percentiles (P50, P95, P99)
- [ ] Active user count and session duration
- [ ] Resource utilization (CPU, memory, disk)
- [ ] Database connection pool status
- [ ] Redis cache hit rate
- [ ] External API call success rate
- [ ] Application logs for warnings/errors

#### Rollback Triggers

**Immediate Rollback If:**
- Error rate > 2%
- P95 latency > 5s for 5+ consecutive minutes
- Critical exception (data corruption, security breach)
- Application crashes or OOM errors
- Database connection failures

**Rollback Procedure:**
```bash
# Automated rollback script
./scripts/rollback.sh --phase canary --reason "high-error-rate"

# Manual rollback (if automation fails)
# 1. Update load balancer weights
nginx -s reload

# 2. Verify traffic shifted
curl http://monitoring.quantlib.com/traffic-split

# 3. Monitor for 10 minutes
watch -n 10 "curl http://monitoring.quantlib.com/health"
```

#### Go/No-Go Decision

**After 24-48 hours, proceed to Phase 2 if:**
-  All success metrics met
-  No P0/P1 incidents
-  User feedback positive (>80% satisfaction)
-  No security incidents
-  Resource usage stable

**Sign-off Required:** On-call Engineer, Tech Lead

---

### Phase 2: Limited Rollout (25% of Traffic)

**Duration:** 2-3 days  
**Target Users:** 25% of production traffic  
**Monitoring Interval:** Every 30 minutes

#### Implementation

**Traffic Split:**
```yaml
upstream production {
    server prod-v1.quantlib.com weight=75;
    server prod-v2.quantlib.com weight=25;
}
```

#### Success Metrics

| Metric | Target | Warning Threshold | Critical Threshold |
|--------|--------|-------------------|-------------------|
| Error Rate | < 0.5% | > 1% | > 2% |
| P95 Latency | < 2s | > 3s | > 5s |
| P99 Latency | < 5s | > 8s | > 10s |
| Throughput | Stable ±5% | Drop > 10% | Drop > 20% |
| Cache Hit Rate | > 80% | < 70% | < 60% |

#### Additional Monitoring

- **Business Metrics:**
  - Portfolio optimization requests per hour
  - Successful backtesting runs
  - Active concurrent users
  - Data fetch success rate

- **Technical Metrics:**
  - Redis memory usage and eviction rate
  - Database query performance (slow queries)
  - External API latency
  - Disk I/O and network bandwidth

#### Testing Activities

During this phase, actively test:
- [ ] Peak load scenarios (lunch hour, market open/close)
- [ ] Long-running calculations (Monte Carlo 10k+ simulations)
- [ ] Concurrent user sessions (>100 simultaneous users)
- [ ] Data export operations (large CSV downloads)
- [ ] Heavy report generation

#### Go/No-Go Decision

**After 2-3 days, proceed to Phase 3 if:**
-  All Phase 1 criteria still met
-  Performance stable under increased load
-  No degradation in user experience
-  Resource usage predictable and sustainable
-  No unexpected issues discovered

**Sign-off Required:** On-call Engineer, Tech Lead, Product Owner

---

### Phase 3: Majority Rollout (50% of Traffic)

**Duration:** 2-3 days  
**Target Users:** 50% of production traffic  
**Monitoring Interval:** Every hour

#### Implementation

```yaml
upstream production {
    server prod-v1.quantlib.com weight=50;
    server prod-v2.quantlib.com weight=50;
}
```

#### Success Metrics

Same as Phase 2, with additional focus on:
- **Cost Efficiency:** Cloud costs within budget (±10%)
- **Scalability:** Auto-scaling working as expected
- **Data Accuracy:** No calculation discrepancies reported

#### Chaos Engineering (Optional)

If time permits, conduct controlled failure testing:
- [ ] Kill random application instance (verify failover)
- [ ] Simulate database slowdown (connection timeout)
- [ ] Inject network latency (test retry logic)
- [ ] Fill disk to 95% (test storage alerts)

#### Go/No-Go Decision

**After 2-3 days, proceed to Phase 4 if:**
-  System handling 50% load smoothly
-  No performance degradation
-  Auto-scaling working correctly
-  Cost projections accurate
-  Team confidence high

**Sign-off Required:** On-call Engineer, Tech Lead, Product Owner, CFO (cost approval)

---

### Phase 4: Full Rollout (100% of Traffic)

**Duration:** Ongoing  
**Target Users:** 100% of production traffic  
**Monitoring Interval:** Continuous with automated alerts

#### Implementation

```yaml
upstream production {
    server prod-v2.quantlib.com weight=100;  # New version fully live
    # Keep v1 on standby for emergency rollback
    server prod-v1.quantlib.com backup;
}
```

#### Success Metrics

Same as previous phases, with long-term tracking:
- **Reliability:** 99.9% uptime over 30 days
- **Performance:** P95 < 2s, P99 < 5s consistently
- **Cost:** Cloud spend within budget
- **User Satisfaction:** NPS > 50, CSAT > 85%

#### Continuous Monitoring

**Automated Alerts (PagerDuty/AlertManager):**
- Error rate > 1% for 5 minutes → Page on-call
- P95 latency > 3s for 10 minutes → Page on-call
- Any P0 exception → Immediate page
- Database connection pool exhausted → Page on-call
- Disk usage > 85% → Warning email
- Memory usage > 90% → Page on-call

**Daily Health Checks:**
- Review yesterday's metrics summary
- Check for anomalies in usage patterns
- Review slow query logs
- Audit security logs
- Verify backup completion

**Weekly Reviews:**
- Team review of all incidents
- Performance trend analysis
- Cost optimization opportunities
- User feedback review

#### Post-Rollout Activities

**Day 1-7:**
- [ ] Monitor closely (at least hourly checks)
- [ ] Respond to all user feedback promptly
- [ ] Fix any non-critical bugs in hotfix releases
- [ ] Optimize based on production data
- [ ] Update documentation with production learnings

**Day 8-30:**
- [ ] Reduce monitoring frequency (daily checks sufficient)
- [ ] Implement feature improvements based on usage
- [ ] Conduct retrospective with team
- [ ] Update disaster recovery plan
- [ ] Plan next release cycle

---

## Rollback Procedures

### Automated Rollback

**Trigger Conditions:**
```python
# rollback_monitor.py
ROLLBACK_CONDITIONS = {
    "error_rate": 0.02,        # > 2%
    "p95_latency": 5000,       # > 5s
    "availability": 0.99,      # < 99%
    "critical_errors": 1,      # Any critical error
}

def should_rollback(metrics):
    return (
        metrics["error_rate"] > ROLLBACK_CONDITIONS["error_rate"] or
        metrics["p95_latency"] > ROLLBACK_CONDITIONS["p95_latency"] or
        metrics["availability"] < ROLLBACK_CONDITIONS["availability"] or
        metrics["critical_errors"] > 0
    )
```

**Automated Rollback Script:**
```bash
#!/bin/bash
# scripts/auto-rollback.sh

PHASE=$1
REASON=$2

echo "=== AUTOMATED ROLLBACK INITIATED ==="
echo "Phase: $PHASE"
echo "Reason: $REASON"
echo "Time: $(date)"

# 1. Capture current state
./scripts/capture-state.sh > rollback_state_$(date +%s).json

# 2. Switch traffic back to previous version
if [ "$PHASE" = "canary" ]; then
    # Set canary weight to 0
    sed -i 's/weight=5/weight=0/' /etc/nginx/conf.d/upstream.conf
elif [ "$PHASE" = "limited" ]; then
    sed -i 's/weight=25/weight=0/' /etc/nginx/conf.d/upstream.conf
elif [ "$PHASE" = "majority" ]; then
    sed -i 's/weight=50/weight=0/' /etc/nginx/conf.d/upstream.conf
elif [ "$PHASE" = "full" ]; then
    sed -i 's/weight=100/weight=0/' /etc/nginx/conf.d/upstream.conf
fi

nginx -s reload

# 3. Verify rollback
sleep 10
curl http://monitoring.quantlib.com/traffic-split

# 4. Alert team
./scripts/send-alert.sh "Rollback" "$REASON" "critical"

# 5. Create incident ticket
./scripts/create-incident.sh "$REASON"

echo "=== ROLLBACK COMPLETE ==="
```

### Manual Rollback

If automation fails, manual steps:

1. **Log into load balancer**
   ```bash
   ssh admin@lb.quantlib.com
   ```

2. **Edit upstream config**
   ```bash
   sudo vim /etc/nginx/conf.d/upstream.conf
   # Set new version weight to 0
   ```

3. **Reload nginx**
   ```bash
   sudo nginx -s reload
   ```

4. **Verify traffic shifted**
   ```bash
   watch -n 5 "curl -s http://monitoring.quantlib.com/traffic-split | jq '.v2_percentage'"
   ```

5. **Alert team**
   - Post in #incidents Slack channel
   - Create PagerDuty incident
   - Email engineering@quantlib.com

6. **Post-mortem**
   - Document what happened
   - Root cause analysis
   - Action items to prevent recurrence

---

## Communication Plan

### Internal Communication

**Before Rollout:**
- [ ] Email to all engineering (T-7 days)
- [ ] Slack announcement in #general (T-3 days)
- [ ] All-hands meeting update (T-1 day)
- [ ] On-call handoff briefing

**During Rollout:**
- [ ] Slack updates in #deployments every phase
- [ ] Status page updates (status.quantlib.com)
- [ ] Email stakeholders at each phase completion

**After Rollout:**
- [ ] Success announcement (Slack, email)
- [ ] Metrics summary report
- [ ] Retrospective meeting scheduled

### External Communication

**Users:**
- [ ] In-app notification about new features
- [ ] Email newsletter highlighting improvements
- [ ] Blog post (if major release)

**Status Page (status.quantlib.com):**
- Scheduled maintenance windows
- Real-time system status
- Incident history

---

## Success Criteria

### Technical Success
-  99.9% uptime during rollout
-  Error rate < 0.5%
-  P95 latency < 2s
-  No data integrity issues
-  All monitoring and alerting operational

### Business Success
-  User satisfaction maintained (>85%)
-  No critical feature regressions
-  Costs within budget
-  Time-to-rollout within plan (7-14 days)

### Team Success
-  No burnout incidents
-  Knowledge shared across team
-  Documentation updated
-  Process improvements identified

---

## Appendix

### A. Monitoring Dashboards

**Primary Dashboard:** http://grafana.quantlib.com/rollout  
**Alerts:** http://prometheus.quantlib.com/alerts  
**Logs:** http://kibana.quantlib.com

### B. Key Contacts

| Role | Name | Contact |
|------|------|---------|
| Tech Lead | TBD | tech-lead@quantlib.com |
| On-Call Engineer | Rotation | oncall@quantlib.com |
| Product Owner | TBD | product@quantlib.com |
| Security Lead | TBD | security@quantlib.com |

### C. Related Documents

- [Production Deployment Guide](production-deployment.md)
- [On-Call Runbook](oncall-runbook.md)
- [Incident Response Procedures](incident-response.md)
- [Monitoring and Alerting Guide](monitoring-alerting.md)

---

**Document Owner:** DevOps Team  
**Last Updated:** February 23, 2026  
**Next Review:** After full rollout completion
