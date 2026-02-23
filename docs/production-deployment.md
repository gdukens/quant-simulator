# Production Deployment Guide

Complete guide for deploying QuantLib Pro to production environments.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Monitoring Setup](#monitoring-setup)
- [Security Configuration](#security-configuration)
- [Backup and Recovery](#backup-and-recovery)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

### Code and Configuration
- [ ] All tests passing (unit, integration, load)
- [ ] Code linted and formatted (flake8, black)
- [ ] Security scan completed (no critical vulnerabilities)
- [ ] Dependencies up-to-date and audited
- [ ] Environment variables configured
- [ ] API keys and secrets secured
- [ ] Database migrations applied (if applicable)
- [ ] Static assets optimized

### Infrastructure
- [ ] Domain purchased and DNS configured
- [ ] SSL/TLS certificates obtained
- [ ] Load balancer configured
- [ ] CDN setup (if applicable)
- [ ] Firewall rules configured
- [ ] Backup system in place
- [ ] Monitoring and alerting configured
- [ ] Log aggregation setup

### Documentation
- [ ] Deployment documentation complete
- [ ] Disaster recovery plan documented
- [ ] Runbook for common issues
- [ ] Contact list for on-call support

## Docker Deployment

### Local Docker Testing

```bash
# Build image
docker build -t quantlib-pro:latest .

# Run container
docker run -d \
  -p 8501:8501 \
  --name quantlib-app \
  -e APP_ENV=production \
  quantlib-pro:latest

# Check logs
docker logs -f quantlib-app

# Health check
curl http://localhost:8501/_stcore/health
```

### Production Docker Compose

```bash
# Create .env file with production variables
cat > .env <<EOF
APP_ENV=production
LOG_LEVEL=INFO
REDIS_HOST=redis
CACHE_TTL=3600
VERSION=1.0.0
EOF

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Cloud Deployments

### AWS Deployment

**Prerequisites:**
- AWS CLI installed and configured
- IAM user with ECS permissions
- ECR repository access

**Deploy:**
```bash
# Set environment variables
export AWS_REGION=us-east-1
export CLUSTER_NAME=quantlib-pro-cluster
export SERVICE_NAME=quantlib-pro-service

# Run deployment script
chmod +x deploy/aws-deploy.sh
./deploy/aws-deploy.sh
```

**Configuration:**
- **Instance Type**: Fargate with 1 vCPU, 2GB RAM (minimum)
- **Auto Scaling**: Min 1, Max 10 instances
- **Health Check**: /_stcore/health every 30s
- **Timeout**: 300s for long-running calculations

**Monitoring:**
```bash
# View logs
aws logs tail /ecs/quantlib-pro-task --follow --region us-east-1

# Get service status
aws ecs describe-services \
  --cluster quantlib-pro-cluster \
  --services quantlib-pro-service \
  --region us-east-1
```

### GCP Deployment

**Prerequisites:**
- gcloud CLI installed
- GCP project created
- Billing enabled

**Deploy:**
```bash
# Set project
export GCP_PROJECT_ID=your-project-id

# Run deployment
chmod +x deploy/gcp-deploy.sh
./deploy/gcp-deploy.sh
```

**Configuration:**
- **Region**: us-central1 (or closest to users)
- **Memory**: 4Gi
- **CPU**: 2
- **Min Instances**: 1
- **Max Instances**: 10
- **Timeout**: 300s

**Custom Domain:**
```bash
gcloud run domain-mappings create \
  --service quantlib-pro \
  --domain your-domain.com \
  --region us-central1
```

### Azure Deployment

**Prerequisites:**
- Azure CLI installed
- Azure subscription active
- Resource group created

**Deploy:**
```bash
# Login to Azure
az login

# Set variables
export AZURE_RESOURCE_GROUP=quantlib-pro-rg
export AZURE_LOCATION=eastus

# Run deployment
chmod +x deploy/azure-deploy.sh
./deploy/azure-deploy.sh
```

**Configuration:**
- **SKU**: B2 (2 cores, 3.5GB RAM) minimum
- **OS**: Linux
- **Container**: Azure App Service or ACI
- **Scaling**: Auto-scale 1-10 instances

## Monitoring Setup

### Prometheus + Grafana

**Deploy monitoring stack:**
```bash
# Included in docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d grafana prometheus
```

**Access:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

**Key Metrics to Monitor:**
- Request rate (requests/sec)
- Response time (P50, P95, P99)
- Error rate (%)
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Cache hit rate (%)

### Application Insights (Azure)

```bash
# Already configured in azure-deploy.sh
az monitor app-insights component show \
  --app quantlib-pro-insights \
  --resource-group quantlib-pro-rg
```

### CloudWatch (AWS)

Logs automatically available at:
- Log Group: `/ecs/quantlib-pro-task`
- Metrics: ECS > Clusters > quantlib-pro-cluster

### Health Checks

**Liveness Probe** (Is app alive?):
```bash
curl http://localhost:8501/health/live
```

**Readiness Probe** (Ready to serve traffic?):
```bash
curl http://localhost:8501/health/ready
```

**Full Health Check**:
```bash
curl http://localhost:8501/health
```

## Security Configuration

### Environment Variables

**Never commit secrets!** Use environment variables:

```bash
# .env file (add to .gitignore)
APP_ENV=production
SECRET_KEY=<generate-random-key>
ALPHA_VANTAGE_API_KEY=<your-key>
IEX_API_TOKEN=<your-token>
POLYGON_API_KEY=<your-key>
```

### SSL/TLS Configuration

**Option 1: Let's Encrypt (Free)**
```bash
# Using certbot
certbot certonly --standalone -d your-domain.com
```

**Option 2: Cloud Provider**
- AWS: Use ACM (AWS Certificate Manager)
- GCP: Automatic with Cloud Run managed certificates
- Azure: Use App Service Managed Certificates

### Firewall Rules

**Inbound:**
- Port 443 (HTTPS) - from anywhere
- Port 80 (HTTP) - redirect to 443
- SSH (22) - from your IP only

**Outbound:**
- All traffic allowed (for API calls)

### CORS Configuration

If using reverse proxy, configure CORS headers:
```nginx
add_header Access-Control-Allow-Origin "https://your-domain.com";
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
```

## Backup and Recovery

### Data Backup

**Automated Backup Script:**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup data directory
tar -czf $BACKUP_DIR/data.tar.gz data/

# Backup logs
tar -czf $BACKUP_DIR/logs.tar.gz logs/

# Upload to cloud storage (S3 example)
aws s3 cp $BACKUP_DIR s3://quantlib-backups/ --recursive
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### Disaster Recovery

**Recovery Time Objective (RTO)**: 1 hour  
**Recovery Point Objective (RPO)**: 24 hours

**Recovery Steps:**
1. Provision new infrastructure
2. Restore from latest backup
3. Update DNS to new instance
4. Verify health checks
5. Monitor for 24 hours

**Database Recovery** (if using):
```bash
# PostgreSQL example
pg_restore -h localhost -U quantlib -d quantlib_db backup.dump
```

## Performance Tuning

### Application Optimization

**Streamlit Configuration** (`.streamlit/config.toml`):
```toml
[server]
maxUploadSize = 200  # MB
maxMessageSize = 200  # MB
enableCORS = false
enableXsrfProtection = true

[runner]
fastReruns = true
magicEnabled = false

[client]
showErrorDetails = false
toolbarMode = "minimal"

[browser]
gatherUsageStats = false
```

### Caching

**Redis Configuration:**
```bash
# docker-compose.prod.yml already includes Redis
# Use @st.cache_data for Streamlit caching
# Use Redis for cross-instance caching
```

### Resource Limits

**Docker:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

**Kubernetes:**
```yaml
resources:
  requests:
    cpu: "1000m"
    memory: "2Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

## Troubleshooting

### Common Issues

**1. Container Won't Start**
```bash
# Check logs
docker logs quantlib-app

# Common causes:
# - Missing environment variables
# - Port already in use
# - Insufficient memory
```

**2. Health Check Failing**
```bash
# Test health endpoint
curl -v http://localhost:8501/_stcore/health

# Check Streamlit is running
docker exec -it quantlib-app ps aux | grep streamlit
```

**3. Out of Memory**
```bash
# Check memory usage
docker stats quantlib-app

# Solution: Increase memory limit or optimize code
docker update --memory 4g quantlib-app
```

**4. Slow Performance**
```bash
# Enable profiling
export STREAMLIT_PROFILER_ENABLED=true

# Check database query performance
# Add caching to expensive operations
```

**5. SSL Certificate Issues**
```bash
# Verify certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Renew Let's Encrypt cert
certbot renew
```

### Log Analysis

**View recent errors:**
```bash
# Docker
docker logs quantlib-app --tail 100 | grep ERROR

# AWS CloudWatch
aws logs filter-log-events \
  --log-group-name /ecs/quantlib-pro-task \
  --filter-pattern "ERROR"

# GCP
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 100
```

### Performance Profiling

```python
# Add to code for profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Rollback Procedures

### Docker Rollback
```bash
# Tag previous version
docker tag quantlib-pro:previous quantlib-pro:rollback

# Stop current
docker stop quantlib-app
docker rm quantlib-app

# Start previous version
docker run -d -p 8501:8501 --name quantlib-app quantlib-pro:rollback
```

### Cloud Rollback

**AWS:**
```bash
aws ecs update-service \
  --cluster quantlib-pro-cluster \
  --service quantlib-pro-service \
  --task-definition quantlib-pro-task:PREVIOUS_REVISION
```

**GCP:**
```bash
# Revisions are kept, just rollback
gcloud run services update-traffic quantlib-pro \
  --to-revisions PREVIOUS_REVISION=100
```

**Azure:**
```bash
# Swap slots (if using slots)
az webapp deployment slot swap \
  --name quantlib-pro \
  --resource-group quantlib-pro-rg \
  --slot staging
```

## Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- [ ] Review error logs
- [ ] Check disk space
- [ ] Verify backups
- [ ] Review performance metrics

**Monthly:**
- [ ] Update dependencies
- [ ] Security scan
- [ ] Load test
- [ ] Review and optimize queries
- [ ] Clean up old logs and data

**Quarterly:**
- [ ] Disaster recovery test
- [ ] Capacity planning review
- [ ] Documentation update
- [ ] Security audit

### On-Call Procedures

**Critical Incident:**
1. Check health endpoints
2. Review recent logs
3. Check monitoring dashboards
4. Rollback if necessary
5. Escalate if needed
6. Document incident

**Post-Incident:**
1. Root cause analysis
2. Implement fixes
3. Update runbook
4. Team debrief

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [AWS ECS Guide](https://docs.aws.amazon.com/ecs/)
- [GCP Cloud Run Docs](https://cloud.google.com/run/docs)
- [Azure App Service Docs](https://docs.microsoft.com/en-us/azure/app-service/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)

**Questions?** Open an issue on GitHub or contact the team.
