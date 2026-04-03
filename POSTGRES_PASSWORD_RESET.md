#  PostgreSQL Password Reset & Management Guide

##  **Current Configuration**
```env
POSTGRES_PASSWORD=changeme
POSTGRES_USER=quantlib
DATABASE_PASSWORD=changeme
```

##  **Method 1: Simple Password Change (Recommended)**

### Step 1: Update Environment Variables
```powershell
# Edit .env file - change BOTH passwords to match
POSTGRES_PASSWORD=your_new_secure_password
DATABASE_PASSWORD=your_new_secure_password
```

### Step 2: Recreate Container with New Password
```powershell
# Stop and remove the old container
docker stop quantlib-postgres quantlib-timescaledb
docker rm quantlib-postgres quantlib-timescaledb

# Remove old volumes ( This will delete data!)
docker volume rm advancedquant_postgres-data advancedquant_timescale-data

# Start fresh with new password
docker-compose -f docker-compose.prod.yml up -d postgres timescaledb
```

##  **Method 2: Reset Password in Running Container**

### Step 1: Connect to Running Container
```powershell
# Connect to the PostgreSQL container
docker exec -it quantlib-postgres psql -U quantlib -d quantlib_db
```

### Step 2: Change Password from SQL
```sql
-- Change the password for user 'quantlib'
ALTER USER quantlib PASSWORD 'your_new_secure_password';

-- Verify the change
\du
\q
```

### Step 3: Update .env File to Match
```env
POSTGRES_PASSWORD=your_new_secure_password
DATABASE_PASSWORD=your_new_secure_password
```

##  **Method 3: Password Reset Script (Automated)**

### Create Password Reset Script
```powershell
# Create: scripts/reset-postgres-password.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$NewPassword
)

Write-Host " Resetting PostgreSQL Password..." -ForegroundColor Cyan

# Update .env file
$envPath = ".env"
$content = Get-Content $envPath
$content = $content -replace "POSTGRES_PASSWORD=.*", "POSTGRES_PASSWORD=$NewPassword"
$content = $content -replace "DATABASE_PASSWORD=.*", "DATABASE_PASSWORD=$NewPassword"
Set-Content -Path $envPath -Value $content

Write-Host " Updated .env file" -ForegroundColor Green

# Reset container
Write-Host " Recreating PostgreSQL container..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down postgres timescaledb
docker volume rm advancedquant_postgres-data advancedquant_timescale-data -f 2>$null
docker-compose -f docker-compose.prod.yml up -d postgres timescaledb

Write-Host " PostgreSQL password reset complete!" -ForegroundColor Green
Write-Host "New password: $NewPassword" -ForegroundColor White
```

##  **Method 4: Preserve Data During Password Change**

### Step 1: Backup Data First
```powershell
# Create backup
docker exec quantlib-postgres pg_dump -U quantlib quantlib_db > backup.sql
```

### Step 2: Change Password and Restore
```powershell
# Stop containers
docker-compose -f docker-compose.prod.yml down

# Update .env with new password
# POSTGRES_PASSWORD=new_secure_password

# Remove old volumes
docker volume rm advancedquant_postgres-data

# Start with new password
docker-compose -f docker-compose.prod.yml up -d postgres

# Restore data
docker exec -i quantlib-postgres psql -U quantlib quantlib_db < backup.sql
```

##  **Quick Commands**

```powershell
# Test current connection
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5433, 
    database='quantlib_db', user='quantlib', 
    password='changeme'
)
print(' Connection successful!')
conn.close()
"

# Reset with secure password
.\scripts\reset-postgres-password.ps1 -NewPassword "SecurePass123!"

# Verify new connection  
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5433,
    database='quantlib_db', user='quantlib',
    password='SecurePass123!'
)
print(' New password works!')
conn.close()
"
```

##  **Important Notes**

1. ** Data Loss Warning**: Methods that remove Docker volumes will delete all data
2. ** Security**: Never use 'changeme' or simple passwords in production
3. ** Documentation**: Update all connection strings after password change
4. ** Restart Required**: Applications need restart to use new passwords
5. ** Test First**: Always test the new password before deploying

##  **Recommended Production Password**

```env
# Generate secure password
POSTGRES_PASSWORD=QLP_$(Get-Random -Minimum 100000 -Maximum 999999)_$(Get-Date -Format "yyyy")
```

**Example**: `QLP_847392_2026`