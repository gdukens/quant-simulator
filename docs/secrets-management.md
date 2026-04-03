# Secrets Management Guide

Comprehensive guide for managing secrets and API keys in production.

## Table of Contents

- [Overview](#overview)
- [Secrets Hierarchy](#secrets-hierarchy)
- [Local Development](#local-development)
- [Cloud Secrets Management](#cloud-secrets-management)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Rotation Procedures](#rotation-procedures)
- [Emergency Response](#emergency-response)

## Overview

**Never commit secrets to version control!**

This guide covers secure management of:
- API keys (market data providers)
- Database credentials
- Encryption keys
- Authentication tokens
- Cloud provider credentials
- Third-party service keys

## Secrets Hierarchy

### Critical (Tier 1)
Compromising these gives full system access:
- `SECRET_KEY` - Encryption master key
- `ENCRYPTION_KEY` - Fernet encryption key
- `JWT_SECRET_KEY` - Authentication signing key
- Database passwords
- Cloud provider credentials (AWS/GCP/Azure)

**Rotation: Every 90 days**  
**Access: Admin only**

### High (Tier 2)
Service-specific credentials:
- Market data API keys (Alpha Vantage, IEX, Polygon)
- Email/SMTP credentials
- Monitoring service keys (Sentry, New Relic)
- Redis password

**Rotation: Every 180 days**  
**Access: Developers with need-to-know**

### Medium (Tier 3)
Configuration and non-sensitive keys:
- Grafana admin password
- Prometheus configuration
- Feature flags

**Rotation: Annually**  
**Access: All developers**

## Local Development

### Initial Setup

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Generate secure keys:**
```bash
# SECRET_KEY (64-character hex)
python -c "import secrets; print(secrets.token_hex(64))"

# ENCRYPTION_KEY (Fernet key)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# JWT_SECRET_KEY (64-character hex)
python -c "import secrets; print(secrets.token_hex(64))"
```

3. **Fill in API keys:**
- Get free API keys from providers (see [API Key Sources](#api-key-sources))
- Add to `.env` file
- Verify `.env` is in `.gitignore`

### Verify `.gitignore`

```bash
# Check if .env is ignored
grep "^\.env$" .gitignore || echo ".env" >> .gitignore
```

### Testing with Mock Secrets

For tests, use mock values:
```bash
# .env.test
USE_MOCK_DATA=true
ALPHA_VANTAGE_API_KEY=demo
DATABASE_URL=sqlite:///:memory:
REDIS_HOST=localhost
```

## Cloud Secrets Management

### AWS Secrets Manager

**Store secrets:**
```bash
# Store individual secret
aws secretsmanager create-secret \
  --name quantlib/prod/secret-key \
  --secret-string "your-secret-value" \
  --region us-east-1

# Store multiple secrets as JSON
aws secretsmanager create-secret \
  --name quantlib/prod/api-keys \
  --secret-string '{
    "ALPHA_VANTAGE_API_KEY": "your-key",
    "IEX_API_TOKEN": "your-token",
    "POLYGON_API_KEY": "your-key"
  }' \
  --region us-east-1
```

**Retrieve secrets in application:**
```python
import boto3
import json
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name="us-east-1"):
    """Retrieve secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    
    return json.loads(get_secret_value_response['SecretString'])

# Usage
secrets = get_secret('quantlib/prod/api-keys')
ALPHA_VANTAGE_API_KEY = secrets['ALPHA_VANTAGE_API_KEY']
```

**IAM Policy for ECS Task:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:quantlib/*"
      ]
    }
  ]
}
```

### GCP Secret Manager

**Store secrets:**
```bash
# Create secret
echo -n "your-secret-value" | gcloud secrets create quantlib-secret-key \
  --data-file=- \
  --replication-policy="automatic"

# Add version
echo -n "new-secret-value" | gcloud secrets versions add quantlib-secret-key \
  --data-file=-
```

**Retrieve secrets in application:**
```python
from google.cloud import secretmanager

def get_secret(project_id, secret_id, version_id="latest"):
    """Retrieve secret from GCP Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

# Usage
ALPHA_VANTAGE_API_KEY = get_secret("your-project-id", "alpha-vantage-key")
```

**Grant Cloud Run access:**
```bash
gcloud secrets add-iam-policy-binding quantlib-secret-key \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Azure Key Vault

**Store secrets:**
```bash
# Create Key Vault
az keyvault create \
  --name quantlib-keyvault \
  --resource-group quantlib-pro-rg \
  --location eastus

# Store secret
az keyvault secret set \
  --vault-name quantlib-keyvault \
  --name secret-key \
  --value "your-secret-value"
```

**Retrieve secrets in application:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_secret(vault_url, secret_name):
    """Retrieve secret from Azure Key Vault."""
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    secret = client.get_secret(secret_name)
    return secret.value

# Usage
vault_url = "https://quantlib-keyvault.vault.azure.net/"
ALPHA_VANTAGE_API_KEY = get_secret(vault_url, "alpha-vantage-key")
```

**Grant App Service access:**
```bash
# Enable managed identity on App Service
az webapp identity assign \
  --name quantlib-pro \
  --resource-group quantlib-pro-rg

# Grant access to Key Vault
az keyvault set-policy \
  --name quantlib-keyvault \
  --object-id <MANAGED_IDENTITY_OBJECT_ID> \
  --secret-permissions get list
```

## CI/CD Integration

### GitHub Actions Secrets

**Add secrets to repository:**

1. Go to repository Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `GCP_SA_KEY` (service account JSON)
   - `AZURE_CREDENTIALS` (JSON)

**Use in workflow:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
```

### Environment-Specific Secrets

**Create environment-specific secrets:**
- `production/SECRET_KEY`
- `staging/SECRET_KEY`
- `development/SECRET_KEY`

**Use in workflow:**
```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production  # Uses production secrets
    steps:
      - name: Deploy
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
        run: ./deploy.sh
```

## Best Practices

### 1. Never Hardcode Secrets
 **Bad:**
```python
API_KEY = "abc123xyz789"
```

 **Good:**
```python
import os
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
if not API_KEY:
    raise ValueError("ALPHA_VANTAGE_API_KEY not set")
```

### 2. Use Environment Variables
```python
import os
from dotenv import load_dotenv

# Load .env file in development
if os.getenv('APP_ENV') != 'production':
    load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
```

### 3. Validate Secrets at Startup
```python
REQUIRED_SECRETS = [
    'SECRET_KEY',
    'ENCRYPTION_KEY',
    'DATABASE_PASSWORD',
    'ALPHA_VANTAGE_API_KEY',
]

def validate_secrets():
    """Validate all required secrets are present."""
    missing = [s for s in REQUIRED_SECRETS if not os.getenv(s)]
    if missing:
        raise ValueError(f"Missing required secrets: {', '.join(missing)}")

validate_secrets()
```

### 4. Separate Secrets by Environment
```
.env.development
.env.staging
.env.production
```

### 5. Use Strong Random Values
```python
import secrets

# Generate 32-byte (256-bit) key
secret_key = secrets.token_hex(32)

# Generate URL-safe token
api_token = secrets.token_urlsafe(32)
```

### 6. Limit Secret Access
- Principle of least privilege
- Use IAM roles instead of credentials when possible
- Audit secret access regularly

### 7. Encrypt Secrets at Rest
All cloud secret managers encrypt by default. For local:
```bash
# Encrypt .env file with GPG
gpg --symmetric --cipher-algo AES256 .env
# Creates .env.gpg (commit this, not .env)

# Decrypt
gpg --decrypt .env.gpg > .env
```

### 8. Use Secret Scanning
Enable GitHub secret scanning:
1. Settings > Code security and analysis
2. Enable "Secret scanning"
3. GitHub will alert on committed secrets

## Rotation Procedures

### Database Password Rotation

```bash
# 1. Generate new password
NEW_PASSWORD=$(python -c "import secrets; print(secrets.token_hex(16))")

# 2. Update database
psql -c "ALTER USER quantlib WITH PASSWORD '$NEW_PASSWORD';"

# 3. Update secrets manager
aws secretsmanager update-secret \
  --secret-id quantlib/prod/database-password \
  --secret-string "$NEW_PASSWORD"

# 4. Restart application (picks up new password)
kubectl rollout restart deployment/quantlib-pro
```

### API Key Rotation

```bash
# 1. Obtain new API key from provider
NEW_API_KEY="new-key-from-provider"

# 2. Update secrets manager
gcloud secrets versions add alpha-vantage-key \
  --data-file=<(echo -n "$NEW_API_KEY")

# 3. Update application environment
# (Cloud Run will pick up new version automatically)

# 4. Revoke old key after verification
```

### Automated Rotation (AWS Example)

```python
import boto3
import secrets

def rotate_secret(secret_name):
    """Rotate secret in AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    
    # Generate new secret
    new_secret = secrets.token_hex(32)
    
    # Update secret
    client.update_secret(
        SecretId=secret_name,
        SecretString=new_secret
    )
    
    # Trigger application restart
    # (implementation depends on deployment)
    
    return new_secret
```

## Emergency Response

### Secret Compromise Checklist

If a secret is compromised:

1. **Immediate Actions (< 5 minutes)**
   - [ ] Rotate compromised secret immediately
   - [ ] Revoke old secret/key
   - [ ] Check logs for unauthorized access
   - [ ] Alert security team

2. **Short-term Response (< 1 hour)**
   - [ ] Identify scope of compromise
   - [ ] Update all affected systems
   - [ ] Force logout of all users (if auth compromised)
   - [ ] Review recent activity logs

3. **Investigation (< 24 hours)**
   - [ ] Determine how secret was exposed
   - [ ] Identify all affected systems
   - [ ] Check for data exfiltration
   - [ ] Document incident

4. **Remediation (< 1 week)**
   - [ ] Fix root cause
   - [ ] Improve secret management practices
   - [ ] Update documentation
   - [ ] Team post-mortem

### Quick Rotation Commands

**Rotate all critical secrets:**
```bash
#!/bin/bash
# emergency-rotation.sh

echo "=== Emergency Secret Rotation ==="

# Rotate SECRET_KEY
NEW_SECRET=$(python -c "import secrets; print(secrets.token_hex(64))")
aws secretsmanager update-secret \
  --secret-id quantlib/prod/secret-key \
  --secret-string "$NEW_SECRET"

# Rotate ENCRYPTION_KEY
NEW_ENCRYPTION=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
aws secretsmanager update-secret \
  --secret-id quantlib/prod/encryption-key \
  --secret-string "$NEW_ENCRYPTION"

# Rotate JWT_SECRET_KEY
NEW_JWT=$(python -c "import secrets; print(secrets.token_hex(64))")
aws secretsmanager update-secret \
  --secret-id quantlib/prod/jwt-secret-key \
  --secret-string "$NEW_JWT"

echo "=== Rotation Complete - Restart Application ==="
```

## API Key Sources

### Market Data Providers

**Alpha Vantage** (Free tier: 25 requests/day)
- URL: https://www.alphavantage.co/support/#api-key
- Sign up for free API key
- Premium: $49/month for 500 requests/day

**IEX Cloud** (Free tier available)
- URL: https://iexcloud.io/console/tokens
- Create account and get token
- Premium: Starts at $9/month

**Polygon.io** (Free tier: 5 requests/minute)
- URL: https://polygon.io/dashboard/api-keys
- Sign up and generate API key
- Premium: Starts at $29/month

**Finnhub** (Free tier: 60 requests/minute)
- URL: https://finnhub.io/dashboard
- Create account and get API key
- Premium: Starts at $59/month

**Quandl/Nasdaq Data Link** (Free datasets available)
- URL: https://data.nasdaq.com/account/api
- Sign up and copy API key
- Premium: Varies by dataset

### Monitoring Services

**Sentry** (Error Tracking)
- URL: https://sentry.io
- Free tier: 5,000 events/month
- Get DSN from project settings

**New Relic** (APM)
- URL: https://newrelic.com
- Free tier available
- Get license key from account settings

## Secrets Checklist

Before production deployment:

- [ ] All secrets generated securely
- [ ] No secrets in version control
- [ ] `.env` in `.gitignore`
- [ ] Secrets stored in cloud secret manager
- [ ] IAM policies configured correctly
- [ ] Secrets validated at application startup
- [ ] Monitoring for secret access configured
- [ ] Rotation schedule documented
- [ ] Emergency rotation procedure tested
- [ ] Team trained on secret management

---

**Remember: Treat secrets like passwords - never share, never commit, rotate regularly.**

