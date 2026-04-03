# PostgreSQL Password Reset Script for QuantLib Pro
# Usage: .\reset-postgres-password.ps1 -NewPassword "YourSecurePassword"

param(
    [Parameter(Mandatory=$true)]
    [string]$NewPassword,
    
    [switch]$PreserveData,
    [switch]$DryRun
)

function Write-ResetLog {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Test-PostgreSQLConnection {
    param([string]$Password)
    
    try {
        $testScript = @"
import psycopg2
import sys
try:
    conn = psycopg2.connect(
        host='localhost', 
        port=5433,
        database='quantlib_db', 
        user='quantlib', 
        password='$Password'
    )
    conn.close()
    print('SUCCESS')
except Exception as e:
    print('FAILED:', str(e))
    sys.exit(1)
"@
        
        $result = python -c $testScript 2>$null
        return $result -eq "SUCCESS"
    } catch {
        return $false
    }
}

function Update-EnvFile {
    param([string]$Password)
    
    Write-ResetLog "Updating .env file..." "Yellow" ""
    
    # Look for .env in parent directory if not in current directory
    $envPath = ".env"
    if (!(Test-Path $envPath)) {
        $envPath = "../.env"
    }
    if (!(Test-Path $envPath)) {
        Write-ResetLog " .env file not found in current or parent directory!" "Red" ""
        return $false
    }
    
    try {
        $content = Get-Content $envPath
        $content = $content -replace "POSTGRES_PASSWORD=.*", "POSTGRES_PASSWORD=$Password"
        $content = $content -replace "DATABASE_PASSWORD=.*", "DATABASE_PASSWORD=$Password"
        $content = $content -replace "DATABASE_URL=postgresql://quantlib:.*@", "DATABASE_URL=postgresql://quantlib:$Password@"
        
        if ($DryRun) {
            Write-ResetLog " Would update .env with new password" "Yellow" ""
        } else {
            Set-Content -Path $envPath -Value $content
            Write-ResetLog " .env file updated successfully" "Green" ""
        }
        return $true
    } catch {
        Write-ResetLog " Failed to update .env: $_" "Red" ""
        return $false
    }
}

function Backup-PostgreSQLData {
    Write-ResetLog "Creating backup..." "Yellow" ""
    
    $backupFile = "postgres_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    
    try {
        if ($DryRun) {
            Write-ResetLog " Would create backup: $backupFile" "Yellow" ""
        } else {
            docker exec quantlib-postgres pg_dump -U quantlib quantlib_db > $backupFile 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ResetLog " Backup created: $backupFile" "Green" ""
                return $backupFile
            } else {
                Write-ResetLog " Backup failed, continuing without backup..." "Yellow" ""
                return $null
            }
        }
    } catch {
        Write-ResetLog " Backup failed: $_" "Yellow" ""
        return $null
    }
}

function Reset-PostgreSQLContainer {
    param([string]$BackupFile = $null)
    
    Write-ResetLog "Resetting PostgreSQL containers..." "Yellow" ""
    
    if ($DryRun) {
        Write-ResetLog " Would stop and recreate PostgreSQL containers" "Yellow" ""
        return $true
    }
    
    try {
        # Stop containers
        Write-ResetLog "Stopping containers..." "Gray" "⏹"
        docker-compose -f docker-compose.prod.yml down postgres timescaledb 2>$null
        
        # Remove volumes if not preserving data
        if (!$PreserveData) {
            Write-ResetLog "Removing old volumes..." "Gray" ""
            docker volume rm advancedquant_postgres-data advancedquant_timescale-data 2>$null
        }
        
        # Start with new password
        Write-ResetLog "Starting containers with new password..." "Blue" ""
        docker-compose -f docker-compose.prod.yml up -d postgres timescaledb
        
        # Wait for containers to be ready
        Write-ResetLog "Waiting for PostgreSQL to be ready..." "Blue" "⏳"
        $retries = 0
        do {
            Start-Sleep -Seconds 3
            $ready = docker exec quantlib-postgres pg_isready -U quantlib 2>$null
            $retries++
        } while ($ready -notlike "*accepting connections*" -and $retries -lt 20)
        
        if ($retries -ge 20) {
            Write-ResetLog " PostgreSQL failed to start within timeout" "Red" ""
            return $false
        }
        
        # Restore backup if available and preserving data
        if ($BackupFile -and (Test-Path $BackupFile) -and $PreserveData) {
            Write-ResetLog "Restoring data from backup..." "Blue" ""
            Get-Content $BackupFile | docker exec -i quantlib-postgres psql -U quantlib quantlib_db 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ResetLog " Data restored successfully" "Green" ""
            } else {
                Write-ResetLog " Data restoration had issues" "Yellow" ""
            }
        }
        
        return $true
    } catch {
        Write-ResetLog " Container reset failed: $_" "Red" ""
        return $false
    }
}

# Main execution
Write-ResetLog "PostgreSQL Password Reset Tool" "Cyan" ""
Write-ResetLog "═══════════════════════════════" "Gray"

if ($DryRun) {
    Write-ResetLog " DRY RUN MODE - No changes will be made" "Yellow" ""
}

# Validate password strength
if ($NewPassword.Length -lt 8) {
    Write-ResetLog " Password too short! Minimum 8 characters required." "Red" ""
    exit 1
}

Write-ResetLog "New password: $NewPassword" "White" ""
Write-ResetLog "Preserve data: $PreserveData" "White" ""

# Test current connection
Write-ResetLog "Testing current connection..." "Blue" ""

# Look for .env in parent directory if not in current directory
$envPath = ".env"
if (!(Test-Path $envPath)) {
    $envPath = "../.env"
}

if (Test-Path $envPath) {
    $currentPassword = (Get-Content $envPath | Where-Object { $_ -match "POSTGRES_PASSWORD=" }) -replace "POSTGRES_PASSWORD=", ""
    if (Test-PostgreSQLConnection -Password $currentPassword) {
        Write-ResetLog " Current connection working" "Green" ""
    } else {
        Write-ResetLog " Current connection failed - proceeding with reset" "Yellow" ""
    }
} else {
    Write-ResetLog " .env file not found - proceeding with reset" "Yellow" ""
}

# Create backup if preserving data
$backupFile = $null
if ($PreserveData) {
    $backupFile = Backup-PostgreSQLData
}

# Update .env file
if (!(Update-EnvFile -Password $NewPassword)) {
    exit 1
}

# Reset containers
if (!(Reset-PostgreSQLContainer -BackupFile $backupFile)) {
    exit 1
}

# Test new connection
if (!$DryRun) {
    Write-ResetLog "Testing new connection..." "Blue" ""
    Start-Sleep -Seconds 2
    
    if (Test-PostgreSQLConnection -Password $NewPassword) {
        Write-ResetLog " Password reset successful!" "Green" ""
        Write-ResetLog " New password is working correctly!" "Green" ""
    } else {
        Write-ResetLog " Password reset failed - connection test failed" "Red" ""
        exit 1
    }
}

Write-ResetLog "" 
Write-ResetLog "Password Reset Complete!" "Green" ""
Write-ResetLog "═══════════════════════════" "Gray"

if (!$DryRun) {
    Write-ResetLog "Next steps:" "Cyan" ""
    Write-ResetLog "1. Update any application connection strings" "White" ""
    Write-ResetLog "2. Restart applications that use the database" "White" ""
    Write-ResetLog "3. Test all database connections" "White" ""
    
    if ($backupFile) {
        Write-ResetLog "4. Remove backup file when no longer needed: $backupFile" "White" ""
    }
}