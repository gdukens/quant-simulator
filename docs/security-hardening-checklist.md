# Security Hardening Checklist

Comprehensive security validation checklist for QuantLib Pro production deployment.

## Table of Contents

- [Overview](#overview)
- [Pre-Deployment Security Audit](#pre-deployment-security-audit)
- [OWASP Top 10 Validation](#owasp-top-10-validation)
- [Dependency Security](#dependency-security)
- [Authentication & Authorization](#authentication--authorization)
- [Secrets Management](#secrets-management)
- [Network Security](#network-security)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Data Protection](#data-protection)
- [Penetration Testing](#penetration-testing)
- [Security Monitoring](#security-monitoring)

---

## Overview

**Security Objectives:**
- Protect user data and privacy
- Prevent unauthorized access
- Detect and respond to security incidents
- Maintain compliance with industry standards
- Regular security assessments

**Security Standards:**
- OWASP Top 10 (2021)
- CWE Top 25
- PCI DSS (if handling payments)
- GDPR (for EU users)

---

## Pre-Deployment Security Audit

### Application Security

- [ ] **Code Review**
  - Static analysis completed (Bandit, SonarQube)
  - No critical or high severity issues
  - Security-sensitive code manually reviewed
  - Third-party libraries vetted

- [ ] **Dependency Scanning**
  - All dependencies scanned for vulnerabilities
  - No critical vulnerabilities (CVE score > 9.0)
  - High vulnerabilities documented with mitigation plan
  - Dependency update plan in place

- [ ] **Configuration Security**
  - No hardcoded secrets in code
  - All sensitive config in environment variables
  - Production configs reviewed
  - Debug mode disabled in production

- [ ] **Error Handling**
  - Generic error messages to users
  - Detailed errors logged server-side only
  - No stack traces exposed in production
  - Error monitoring configured

### Infrastructure Security

- [ ] **Server Hardening**
  - OS security patches applied
  - Unnecessary services disabled
  - Firewall configured (only required ports open)
  - SSH key-based authentication only

- [ ] **Container Security**
  - Base images from trusted sources
  - No root user in containers
  - Minimal container images (distroless if possible)
  - Container vulnerability scanning passed

- [ ] **Network Security**
  - Internal services not exposed publicly
  - Database not accessible from internet
  - Redis not accessible from internet
  - VPN/bastion for admin access

- [ ] **Access Control**
  - Principle of least privilege applied
  - Role-based access control (RBAC)
  - Multi-factor authentication (MFA) enabled
  - Regular access reviews scheduled

---

## OWASP Top 10 Validation

### A01:2021 - Broken Access Control

- [ ] **Authorization Checks**
  - Every endpoint validates user permissions
  - Direct object references validated
  - User can only access their own data
  - Admin functions require admin role

**Test:**
```bash
# Try accessing another user's portfolio
curl -H "Authorization: Bearer USER_A_TOKEN" \
  http://localhost:8501/api/portfolio/user_b_portfolio_id

# Expected: 403 Forbidden
```

### A02:2021 - Cryptographic Failures

- [ ] **Data Encryption**
  - Passwords hashed with bcrypt/Argon2
  - Sensitive data encrypted at rest
  - TLS 1.2+ for data in transit
  - Strong encryption algorithms (AES-256)

**Test:**
```python
# Verify password hashing
from quantlib_pro.auth import hash_password
hashed = hash_password("test123")
assert hashed != "test123"
assert len(hashed) > 60  # bcrypt produces 60-char hash
```

### A03:2021 - Injection

- [ ] **SQL Injection Prevention**
  - Parameterized queries only (no string concatenation)
  - ORM properly configured
  - Input validation on all user inputs
  - Database user has minimal privileges

**Test:**
```python
# Try SQL injection
malicious_input = "'; DROP TABLE users; --"
result = db.execute("SELECT * FROM portfolios WHERE name = ?", (malicious_input,))
# Should safely handle the input
```

- [ ] **Command Injection Prevention**
  - No shell commands with user input
  - If unavoidable, strict input validation
  - Use subprocess with argument lists, not shell=True

**Test:**
```python
# Ensure no shell injection
user_file = "../../../etc/passwd"
# Should validate and reject
```

### A04:2021 - Insecure Design

- [ ] **Security Architecture**
  - Threat model documented
  - Security controls at each layer
  - Defense in depth implemented
  - Rate limiting on all public endpoints

**Test:**
```bash
# Rate limiting test
for i in {1..100}; do
  curl http://localhost:8501/api/health
done
# Should get 429 Too Many Requests after threshold
```

### A05:2021 - Security Misconfiguration

- [ ] **Secure Defaults**
  - Default passwords changed
  - Unnecessary features disabled
  - Security headers configured
  - CORS properly configured

**Test:**
```bash
# Check security headers
curl -I https://quantlib.com
# Should see:
# Strict-Transport-Security: max-age=31536000
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: default-src 'self'
```

### A06:2021 - Vulnerable Components

- [ ] **Component Management**
  - Dependency versions pinned
  - No known vulnerabilities (CVE database checked)
  - Automated vulnerability scanning
  - Update process documented

**Test:**
```bash
# Scan for vulnerabilities
pip-audit
safety check
```

### A07:2021 - Identification & Authentication Failures

- [ ] **Authentication Security**
  - Strong password policy (min 12 chars, complexity)
  - MFA available/required
  - Session timeout configured (30 min idle)
  - Account lockout after failed attempts

**Test:**
```python
# Test weak password rejection
response = register_user("user@test.com", "12345")
assert response.status == 400
assert "weak password" in response.message.lower()
```

### A08:2021 - Software and Data Integrity Failures

- [ ] **Integrity Validation**
  - Dependencies verified (checksums/signatures)
  - CI/CD pipeline secured
  - Code signing implemented
  - Audit trail for all changes

**Test:**
```bash
# Verify dependency integrity
pip install --require-hashes -r requirements.txt
```

### A09:2021 - Security Logging & Monitoring Failures

- [ ] **Logging & Monitoring**
  - All authentication events logged
  - All authorization failures logged
  - Suspicious activity alerts configured
  - Log tampering prevention

**Test:**
```python
# Verify failed login logged
login("user@test.com", "wrong_password")
logs = read_security_logs()
assert "failed_login" in logs[-1]
```

### A10:2021 - Server-Side Request Forgery (SSRF)

- [ ] **SSRF Prevention**
  - URL validation on all external requests
  - Whitelist of allowed domains
  - No requests to internal IPs
  - Timeout on external requests

**Test:**
```python
# Try SSRF attack
malicious_url = "http://169.254.169.254/latest/meta-data/"  # AWS metadata
result = fetch_external_data(malicious_url)
# Should be blocked/rejected
```

---

## Dependency Security

### Vulnerability Scanning

```bash
# Install security tools
pip install pip-audit safety bandit

# Scan dependencies
pip-audit --desc
safety check --json

# Expected: No critical vulnerabilities
```

### Dependency Update Process

- [ ] **Regular Updates**
  - Weekly dependency check scheduled
  - Critical updates within 24 hours
  - Minor updates within 1 week
  - Major updates tested in staging first

### Scan Configuration

**File:** `.github/workflows/security-scan.yml`

```yaml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  push:
    branches: [main, develop]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pip-audit safety
          pip install -r requirements.txt
      
      - name: Run pip-audit
        run: pip-audit --desc
      
      - name: Run safety check
        run: safety check --json
      
      - name: Upload results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

---

## Authentication & Authorization

### Password Security

- [ ] **Password Policy**
  - Minimum 12 characters
  - Complexity requirements (upper, lower, digit, special)
  - No common passwords (check against breached database)
  - Password history (prevent reuse)

**Implementation:**
```python
# quantlib_pro/auth/password_validator.py
import re
from zxcvbn import zxcvbn  # Password strength estimator

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    
    # Length check
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    # Complexity check
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    
    # Strength check (using zxcvbn)
    result = zxcvbn(password)
    if result['score'] < 3:  # 0-4 scale
        return False, f"Password too weak: {result['feedback']['warning']}"
    
    return True, "Password meets requirements"
```

### Session Management

- [ ] **Session Security**
  - Secure session cookies (HttpOnly, Secure, SameSite)
  - Session regeneration after login
  - Absolute timeout (24 hours)
  - Idle timeout (30 minutes)

**Configuration:**
```python
# Session settings
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 86400  # 24 hours
```

### Multi-Factor Authentication (MFA)

- [ ] **MFA Implementation**
  - TOTP (Time-based One-Time Password)
  - Backup codes generated
  - MFA required for admin accounts
  - MFA optional but encouraged for users

---

## Secrets Management

### Secret Storage

- [ ] **No Secrets in Code**
  - Grep for API keys: `grep -r "api_key\s*=\s*['\"][^'\"]+['\"]" .`
  - Grep for passwords: `grep -r "password\s*=\s*['\"][^'\"]+['\"]" .`
  - Check for AWS keys: `grep -r "AKIA[0-9A-Z]{16}" .`
  - Git history checked for leaked secrets

```bash
# Scan for secrets
pip install truffleHog
truffleHog --regex --entropy=True .
```

### Environment Variables

- [ ] **Production Secrets**
  - All secrets in environment variables
  - `.env` file in `.gitignore`
  - Production secrets in secure vault (AWS Secrets Manager, Azure Key Vault)
  - Secrets rotated regularly

**Secret Rotation Schedule:**
| Secret Type | Rotation Frequency |
|-------------|-------------------|
| API Keys | Every 90 days |
| Database Passwords | Every 60 days |
| JWT Secret | Every 30 days |
| Encryption Keys | Every 180 days |

### Secret Scanning

**File:** `.github/workflows/secret-scan.yml`

```yaml
name: Secret Scan

on: [push, pull_request]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Network Security

### Firewall Configuration

- [ ] **Port Access Control**
  - Only required ports open: 80 (HTTP), 443 (HTTPS), 22 (SSH - restricted)
  - Internal ports (5432, 6379, 9090) not exposed
  - SSH restricted to specific IPs or VPN
  - Rate limiting on public ports

**Firewall Rules:**
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH from specific IP only
sudo ufw allow from 203.0.113.0/24 to any port 22

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable firewall
sudo ufw enable
```

### DDoS Protection

- [ ] **DDoS Mitigation**
  - Cloudflare or similar CDN in front
  - Rate limiting configured
  - Connection limits set
  - SYN flood protection enabled

---

## SSL/TLS Configuration

### Certificate Management

- [ ] **SSL Certificate**
  - Valid certificate from trusted CA (Let's Encrypt)
  - Certificate covers all domains/subdomains
  - Auto-renewal configured
  - Certificate expiry monitoring

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d quantlib.com -d www.quantlib.com

# Auto-renewal (cron job)
sudo crontab -e
# Add: 0 0 * * 0 certbot renew --quiet
```

### TLS Configuration

- [ ] **Strong TLS Settings**
  - TLS 1.2 minimum (TLS 1.3 preferred)
  - Strong cipher suites only
  - Perfect Forward Secrecy (PFS)
  - HSTS enabled

**Nginx Configuration:** `/etc/nginx/sites-available/quantlib.conf`

```nginx
server {
    listen 443 ssl http2;
    server_name quantlib.com;
    
    # SSL certificate
    ssl_certificate /etc/letsencrypt/live/quantlib.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/quantlib.com/privkey.pem;
    
    # TLS version
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Strong ciphers only
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    # Perfect Forward Secrecy
    ssl_dhparam /etc/nginx/dhparam.pem;
    
    # HSTS (force HTTPS for 1 year)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';" always;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/quantlib.com/chain.pem;
    
    # Session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name quantlib.com;
    return 301 https://$server_name$request_uri;
}
```

### TLS Validation

- [ ] **SSL Test**
  - Run SSL Labs test: https://www.ssllabs.com/ssltest/
  - Target rating: A or A+
  - No SSL/TLS vulnerabilities detected

```bash
# Test TLS configuration
testssl.sh https://quantlib.com

# Expected: All checks green, no vulnerabilities
```

---

## Data Protection

### Database Security

- [ ] **Database Hardening**
  - Strong database password (20+ chars)
  - Database not accessible from internet
  - SSL/TLS for database connections
  - Regular backups with encryption

**PostgreSQL Security:**
```bash
# Restrict access to localhost only
# File: /etc/postgresql/14/main/pg_hba.conf
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256

# Require SSL
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

### Sensitive Data Encryption

- [ ] **Data at Rest**
  - User passwords hashed (bcrypt with cost 12+)
  - Sensitive fields encrypted (AES-256)
  - Database backups encrypted
  - Encryption keys stored securely

**Encryption Implementation:**
```python
# quantlib_pro/utils/encryption.py
from cryptography.fernet import Fernet
import os

# Load encryption key from environment
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data."""
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return cipher.decrypt(encrypted_data.encode()).decode()
```

### GDPR Compliance

- [ ] **Data Privacy**
  - Privacy policy published
  - Cookie consent implemented
  - User data export available
  - User data deletion available
  - Data retention policy documented

---

## Penetration Testing

### Automated Security Testing

```bash
# Install OWASP ZAP
docker pull owasp/zap2docker-stable

# Run baseline scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://quantlib.com \
  -r penetration-test-report.html

# Review report for vulnerabilities
```

### Manual Testing Checklist

- [ ] **Authentication Testing**
  - Brute force protection verified
  - Session fixation tested
  - Password reset flow tested
  - MFA bypass attempts tested

- [ ] **Authorization Testing**
  - Horizontal privilege escalation tested
  - Vertical privilege escalation tested
  - Direct object reference tested
  - API endpoint authorization tested

- [ ] **Input Validation**
  - SQL injection tested
  - XSS tested
  - Command injection tested
  - Path traversal tested

- [ ] **Business Logic**
  - Negative numbers tested
  - Race conditions tested
  - Parameter tampering tested
  - Workflow bypass tested

### Third-Party Penetration Test

- [ ] **External Audit**
  - Annual penetration test scheduled
  - Reputable security firm contracted
  - All findings documented
  - Remediation plan created

---

## Security Monitoring

### Security Event Logging

- [ ] **Security Logs**
  - All authentication attempts logged
  - All authorization failures logged
  - All admin actions logged
  - Logs centralized and tamper-proof

### Intrusion Detection

- [ ] **IDS/IPS**
  - Fail2Ban configured
  - Unusual traffic patterns monitored
  - Automated IP blocking for attackers
  - Security alerts to on-call

**Fail2Ban Configuration:**
```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
filter = nginx-noscript
logpath = /var/log/nginx/access.log
```

---

## Security Sign-Off

### Pre-Production Checklist

- [ ] All items in this checklist completed
- [ ] Security scan passed (no critical issues)
- [ ] Penetration test completed
- [ ] SSL/TLS configuration validated (A+ rating)
- [ ] Secrets management verified
- [ ] Security monitoring configured
- [ ] Incident response plan reviewed
- [ ] Security team sign-off obtained

### Approval

**Security Lead:** _________________________  
**Date:** _________________________

**Engineering Manager:** _________________________  
**Date:** _________________________

**CTO (for production):** _________________________  
**Date:** _________________________

---

## Ongoing Security

### Regular Activities

**Weekly:**
- Review security logs
- Check for dependency vulnerabilities
- Verify backup encryption

**Monthly:**
- Rotate API keys
- Review access permissions
- Update security documentation

**Quarterly:**
- Penetration testing
- Security training refresher
- Disaster recovery drill

**Annually:**
- Full security audit
- Third-party penetration test
- Update security policies

---

**Last Updated:** February 23, 2026  
**Owner:** Security Team  
**Next Review:** After Week 22 completion
