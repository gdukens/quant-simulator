#  Production Database Setup & Fix
# This script resolves PostgreSQL authentication issues and prepares production database

param(
    [switch]$Fix,
    [switch]$Test,
    [switch]$Reset,
    [switch]$Status
)

function Write-Production {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Test-DatabaseConnection {
    Write-Production "Testing PostgreSQL Connection..." "Yellow" ""
    
    $testScript = @"
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', '5433'),
        database=os.getenv('DATABASE_NAME', 'timeseries_db'),
        user=os.getenv('DATABASE_USER', 'quantlib'),
        password=os.getenv('DATABASE_PASSWORD', 'changeme')
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print(' SUCCESS: PostgreSQL Connected')
    print(f'Version: {version[:50]}...')
    
    # Test creating production schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production_health (
            id SERIAL PRIMARY KEY,
            service VARCHAR(50),
            status VARCHAR(20),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    
    # Insert health check
    cursor.execute('''
        INSERT INTO production_health (service, status) 
        VALUES ('quantlib-pro', 'healthy')
    ''')
    conn.commit()
    
    print(' Production schema created successfully')
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f' FAILED: {e}')
    exit(1)
"@
    
    python -c $testScript
}

function Fix-Database {
    Write-Production "Fixing PostgreSQL Production Authentication..." "Cyan" ""
    
    # Step 1: Stop containers
    Write-Production "Stopping database containers..." "Yellow"
    docker-compose -f docker-compose.prod.yml down postgres timescaledb 2>$null
    
    # Step 2: Clean volumes (fresh start)
    Write-Production "Cleaning database volumes for fresh start..." "Yellow"
    docker volume rm advanced-quant_postgres-data 2>$null
    docker volume rm advanced-quant_timescale-data 2>$null
    
    # Step 3: Create production volumes
    Write-Production "Creating production volumes..." "Blue"
    docker volume create advanced-quant_postgres-data
    docker volume create advanced-quant_timescale-data
    
    # Step 4: Start TimescaleDB (port 5433)
    Write-Production "Starting TimescaleDB production container..." "Green"
    docker-compose -f docker-compose.prod.yml up -d timescaledb
    
    # Step 5: Wait for database to initialize
    Write-Production "Waiting for database initialization (30 seconds)..." "Yellow"
    Start-Sleep -Seconds 30
    
    # Step 6: Test connection
    Write-Production "Testing production database connection..." "Blue"
    Test-DatabaseConnection
}

function Reset-Database {
    Write-Production "RESETTING Database (WARNING: All data will be lost)" "Red" ""
    Write-Host "Are you sure? Type 'RESET' to continue: " -NoNewline -ForegroundColor Yellow
    $confirmation = Read-Host
    
    if ($confirmation -eq "RESET") {
        Fix-Database
        Write-Production "Database reset completed" "Green"
    } else {
        Write-Production "Reset cancelled" "Yellow"
    }
}

function Get-DatabaseStatus {
    Write-Production "Production Database Status:" "Cyan"
    Write-Production "════════════════════════════" "Gray"
    
    # Check containers
    Write-Production "Container Status:" "Yellow"
    $containers = docker ps -f name=timescale --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers
    
    # Check connection
    Write-Production "`nConnection Test:" "Yellow"
    Test-DatabaseConnection
    
    # Show environment
    Write-Production "`nEnvironment Configuration:" "Yellow"
    $env = Get-Content .env | Where-Object { $_ -match "DATABASE_|POSTGRES_" } | ForEach-Object {
        if ($_ -notmatch "PASSWORD") { Write-Host "  $_" }
        else { Write-Host "  $($_.Split('=')[0])=****" }
    }
}

# Main execution
switch ($true) {
    $Status { Get-DatabaseStatus }
    $Test { Test-DatabaseConnection }
    $Fix { Fix-Database; Get-DatabaseStatus }
    $Reset { Reset-Database; Get-DatabaseStatus }
    default {
        Write-Production "Production Database Manager" "Cyan"
        Write-Production "═══════════════════════════" "Gray"
        Write-Production ""
        Write-Production "Commands:" "Yellow"
        Write-Production "  -Status    Show current database status"
        Write-Production "  -Test      Test database connection only"
        Write-Production "  -Fix       Fix authentication issues (recommended)"
        Write-Production "  -Reset     Complete database reset (destroys data)"
        Write-Production ""
        Write-Production "Examples:" "Green"
        Write-Production "  .\production-database.ps1 -Status"
        Write-Production "  .\production-database.ps1 -Fix"
        Write-Production "  .\production-database.ps1 -Test"
    }
}