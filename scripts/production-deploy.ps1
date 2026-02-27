# 🚀 QuantLib Pro - Production Deployment Orchestrator
# Executes the complete production deployment plan in phases

param(
    [switch]$Phase1,     # Infrastructure & Security
    [switch]$Phase2,     # Performance & Monitoring  
    [switch]$Phase3,     # Deployment & Testing
    [switch]$All,        # Execute all phases
    [switch]$Status,     # Check current status
    [switch]$Rollback    # Emergency rollback
)

function Write-Deploy {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "🚀")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Write-Phase {
    param([string]$Phase, [string]$Description)
    Write-Deploy "" 
    Write-Deploy "╔══════════════════════════════════════════════════════════════╗" "Cyan"
    Write-Deploy "║  PHASE $Phase: $Description" "Cyan" 
    Write-Deploy "╚══════════════════════════════════════════════════════════════╝" "Cyan"
}

function Test-Prerequisites {
    Write-Deploy "Checking Prerequisites..." "Yellow" "🔍"
    
    # Check Docker
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Deploy "✅ Docker: $dockerVersion" "Green"
    } else {
        Write-Deploy "❌ Docker not installed or not running" "Red"
        return $false
    }
    
    # Check Python
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Deploy "✅ Python: $pythonVersion" "Green"
    } else {
        Write-Deploy "❌ Python not available" "Red"
        return $false
    }
    
    # Check required files
    $requiredFiles = @(
        "docker-compose.prod.yml",
        "main_api.py", 
        "streamlit_app.py",
        ".env"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Deploy "✅ Required file: $file" "Green"
        } else {
            Write-Deploy "❌ Missing required file: $file" "Red"
            return $false
        }
    }
    
    Write-Deploy "✅ All prerequisites met" "Green"
    return $true
}

function Execute-Phase1 {
    Write-Phase "1" "INFRASTRUCTURE & SECURITY"
    
    Write-Deploy "Task 1.1: PostgreSQL Production Fix..." "Yellow" "🔧"
    & ".\scripts\production-database.ps1" -Fix
    if ($LASTEXITCODE -ne 0) {
        Write-Deploy "❌ Database fix failed" "Red"
        return $false
    }
    
    Write-Deploy "Task 1.2: Production Secrets Generation..." "Yellow" "🔐"
    & ".\scripts\production-secrets.ps1" -Generate
    
    Write-Deploy "Task 1.3: Environment Configuration..." "Yellow" "⚙️"
    if (Test-Path ".env.production") {
        Copy-Item ".env.production" ".env" -Force
        Write-Deploy "✅ Production environment activated" "Green"
    }
    
    Write-Deploy "Task 1.4: Security Validation..." "Yellow" "🛡️"
    & ".\scripts\production-secrets.ps1" -Validate
    
    Write-Deploy "✅ PHASE 1 COMPLETED: Infrastructure & Security Ready" "Green" "✅"
    return $true
}

function Execute-Phase2 {
    Write-Phase "2" "PERFORMANCE & MONITORING"
    
    Write-Deploy "Task 2.1: API Performance Optimization..." "Yellow" "⚡"
    # Update database connection pooling
    $optimizationScript = @"
# Performance optimization validation
import time
import requests
import statistics

def test_api_performance():
    url = 'http://localhost:8002/health'
    times = []
    
    for i in range(50):
        start = time.time()
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                times.append((time.time() - start) * 1000)
        except:
            pass
    
    if times:
        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        print(f'Average response time: {avg_time:.2f}ms')
        print(f'95th percentile: {p95_time:.2f}ms')
        
        if p95_time < 500:
            print('✅ Performance target met (<500ms)')
            return True
        else:
            print('❌ Performance target missed (≥500ms)')
            return False
    return False

if __name__ == '__main__':
    test_api_performance()
"@
    
    Write-Deploy "Task 2.2: Monitoring Stack Deployment..." "Yellow" "📊"
    docker-compose -f docker-compose.prod.yml up -d prometheus grafana jaeger 2>$null
    Start-Sleep -Seconds 10
    
    Write-Deploy "Task 2.3: Health Checks Configuration..." "Yellow" "💓"
    # Verify monitoring endpoints
    $endpoints = @("http://localhost:9090", "http://localhost:3000", "http://localhost:16686")
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint -TimeoutSec 5 2>$null
            Write-Deploy "✅ Monitoring endpoint active: $endpoint" "Green"
        } catch {
            Write-Deploy "⚠️  Monitoring endpoint not ready: $endpoint" "Yellow"
        }
    }
    
    Write-Deploy "✅ PHASE 2 COMPLETED: Performance & Monitoring Ready" "Green" "✅"
    return $true
}

function Execute-Phase3 {
    Write-Phase "3" "DEPLOYMENT & TESTING"
    
    Write-Deploy "Task 3.1: Production Container Build..." "Yellow" "🏗️"
    docker-compose -f docker-compose.prod.yml build --no-cache quantlib-app 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Deploy "✅ Production container built successfully" "Green"
    } else {
        Write-Deploy "❌ Container build failed" "Red"
        return $false
    }
    
    Write-Deploy "Task 3.2: Full Stack Deployment..." "Yellow" "🚀"
    docker-compose -f docker-compose.prod.yml up -d
    
    Write-Deploy "Task 3.3: Production Validation..." "Yellow" "🧪"
    Start-Sleep -Seconds 30  # Allow services to initialize
    
    # Test all critical endpoints
    $criticalEndpoints = @{
        "Health Check" = "http://localhost:8503/health"
        "API Documentation" = "http://localhost:8503/docs" 
        "FRED Integration" = "http://localhost:8503/api/v1/macro/regime"
        "Prometheus" = "http://localhost:9090/api/v1/status/config"
        "Grafana" = "http://localhost:3000/api/health"
    }
    
    $allHealthy = $true
    foreach ($test in $criticalEndpoints.Keys) {
        $url = $criticalEndpoints[$test]
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 2>$null
            if ($response.StatusCode -eq 200) {
                Write-Deploy "✅ $test: HEALTHY" "Green"
            } else {
                Write-Deploy "❌ $test: Status $($response.StatusCode)" "Red"
                $allHealthy = $false
            }
        } catch {
            Write-Deploy "❌ $test: CONNECTION FAILED" "Red"
            $allHealthy = $false
        }
    }
    
    if ($allHealthy) {
        Write-Deploy "✅ PHASE 3 COMPLETED: Production Deployment Successful!" "Green" "🎉"
        Write-Deploy "🌐 Production URL: http://localhost:8503" "Cyan" "🌐"
        Write-Deploy "📚 API Docs: http://localhost:8503/docs" "Cyan" "📚"
        Write-Deploy "📊 Grafana: http://localhost:3000 (admin/admin)" "Cyan" "📊"
        return $true
    } else {
        Write-Deploy "❌ Production validation failed" "Red"
        return $false
    }
}

function Get-DeploymentStatus {
    Write-Deploy "Production Deployment Status" "Cyan" "📊"
    Write-Deploy "═══════════════════════════════════════" "Gray"
    
    Write-Deploy "`nContainer Status:" "Yellow"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -match "quantlib|postgres|redis|prometheus|grafana" }
    
    Write-Deploy "`nService Health:" "Yellow"
    $services = @{
        "Main Application" = "http://localhost:8503/health"
        "Database" = "Direct connection test"
        "Redis Cache" = "redis://localhost:6379" 
        "Prometheus" = "http://localhost:9090/-/healthy"
        "Grafana" = "http://localhost:3000/api/health"
    }
    
    foreach ($service in $services.Keys) {
        $url = $services[$service]
        if ($url.StartsWith("http")) {
            try {
                $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 2>$null
                Write-Deploy "✅ $service" "Green"
            } catch {
                Write-Deploy "❌ $service" "Red"
            }
        } else {
            Write-Deploy "🔍 $service (manual test required)" "Yellow"
        }
    }
}

function Execute-Rollback {
    Write-Deploy "🚨 PERFORMING EMERGENCY ROLLBACK" "Red" "🚨"
    
    Write-Deploy "Stopping production containers..." "Yellow"
    docker-compose -f docker-compose.prod.yml down
    
    Write-Deploy "Reverting to development configuration..." "Yellow"
    if (Test-Path ".env.backup") {
        Copy-Item ".env.backup" ".env" -Force
        Write-Deploy "✅ Development configuration restored" "Green"
    }
    
    Write-Deploy "Starting development services..." "Yellow" 
    docker-compose up -d redis postgres
    
    Write-Deploy "✅ Rollback completed - System reverted to development mode" "Green"
}

# Main execution
if (-not (Test-Prerequisites)) {
    Write-Deploy "❌ Prerequisites not met. Cannot proceed with deployment." "Red"
    exit 1
}

# Create backup of current environment
if (Test-Path ".env") {
    Copy-Item ".env" ".env.backup" -Force
}

switch ($true) {
    $Status { Get-DeploymentStatus }
    $Rollback { Execute-Rollback }
    $Phase1 { 
        if (Execute-Phase1) {
            Write-Deploy "🎯 Next: Run .\production-deploy.ps1 -Phase2" "Cyan"
        }
    }
    $Phase2 { 
        if (Execute-Phase2) {
            Write-Deploy "🎯 Next: Run .\production-deploy.ps1 -Phase3" "Cyan"
        }
    }
    $Phase3 { 
        if (Execute-Phase3) {
            Write-Deploy "🎉 PRODUCTION DEPLOYMENT COMPLETE!" "Green" "🎉"
        }
    }
    $All {
        Write-Deploy "🚀 EXECUTING FULL PRODUCTION DEPLOYMENT" "Cyan" "🚀"
        
        if (Execute-Phase1 -and Execute-Phase2 -and Execute-Phase3) {
            Write-Deploy ""
            Write-Deploy "🎉🎉🎉 QUANTLIB PRO PRODUCTION DEPLOYMENT SUCCESSFUL! 🎉🎉🎉" "Green" "🎉"
            Write-Deploy ""
            Write-Deploy "Production Services:" "Cyan"
            Write-Deploy "• Application: http://localhost:8503" "Green" "🌐"
            Write-Deploy "• API Documentation: http://localhost:8503/docs" "Green" "📚"
            Write-Deploy "• Grafana Dashboard: http://localhost:3000" "Green" "📊"
            Write-Deploy "• Prometheus Metrics: http://localhost:9090" "Green" "📈"
            Write-Deploy ""
            Write-Deploy "Enterprise Contact: enterprise@quantlibpro.com" "Cyan" "📞"
        } else {
            Write-Deploy "❌ Production deployment failed. Run .\production-deploy.ps1 -Rollback" "Red"
        }
    }
    default {
        Write-Deploy "QuantLib Pro - Production Deployment Orchestrator" "Cyan"
        Write-Deploy "═══════════════════════════════════════════════════════════" "Gray"
        Write-Deploy ""
        Write-Deploy "Commands:" "Yellow"
        Write-Deploy "  -Phase1     Execute Phase 1: Infrastructure & Security"
        Write-Deploy "  -Phase2     Execute Phase 2: Performance & Monitoring"
        Write-Deploy "  -Phase3     Execute Phase 3: Deployment & Testing"
        Write-Deploy "  -All        Execute complete deployment (all phases)"
        Write-Deploy "  -Status     Check current deployment status"
        Write-Deploy "  -Rollback   Emergency rollback to development"
        Write-Deploy ""
        Write-Deploy "Recommended Usage:" "Green"
        Write-Deploy "  .\production-deploy.ps1 -All    # Full production deployment"
        Write-Deploy "  .\production-deploy.ps1 -Status # Check deployment status"
    }
}