# Production Monitoring Management for QuantLib Pro
# Deploys and manages comprehensive observability stack

param(
    [string]$Action = "help",
    [string]$Service = "",
    [switch]$Deploy,
    [switch]$Status,
    [switch]$Logs,
    [switch]$Reset,
    [switch]$Configure
)

function Write-MonitorLog {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "📊")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Test-MonitoringDependencies {
    Write-MonitorLog "Checking monitoring dependencies..." "Blue" "🔍"
    
    $requirements = @(
        @{Path = "../monitoring/prometheus/prometheus.yml"; Name = "Prometheus Config"}
        @{Path = "../monitoring/prometheus/alert_rules.yml"; Name = "Alert Rules"}
        @{Path = "../monitoring/alertmanager/alertmanager.yml"; Name = "AlertManager Config"}
        @{Path = "../monitoring/grafana/datasources/datasources.yml"; Name = "Grafana Datasources"}
        @{Path = "../monitoring/grafana/dashboards/quantlib-overview.json"; Name = "Grafana Dashboard"}
        @{Path = "../docker-compose.prod.yml"; Name = "Production Docker Compose"}
    )
    
    $allExist = $true
    foreach ($req in $requirements) {
        if (Test-Path $req.Path) {
            Write-MonitorLog "✅ $($req.Name) found" "Green" "✅"
        } else {
            Write-MonitorLog "❌ Missing: $($req.Name) at $($req.Path)" "Red" "❌"
            $allExist = $false
        }
    }
    
    return $allExist
}

function Deploy-MonitoringStack {
    Write-MonitorLog "Deploying QuantLib Pro monitoring stack..." "Cyan" "🚀"
    
    if (!(Test-MonitoringDependencies)) {
        Write-MonitorLog "❌ Missing dependencies. Cannot deploy." "Red" "❌"
        return $false
    }
    
    # Create monitoring directories if they don't exist
    $directories = @(
        "../monitoring/prometheus",
        "../monitoring/alertmanager", 
        "../monitoring/grafana/dashboards",
        "../monitoring/grafana/datasources"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-MonitorLog "📁 Created directory: $dir" "Yellow" "📁"
        }
    }
    
    # Deploy monitoring services
    Write-MonitorLog "🚀 Starting monitoring services..." "Blue" "🚀"
    
    $monitoringServices = @(
        "prometheus",
        "alertmanager", 
        "grafana",
        "node-exporter",
        "cadvisor",
        "redis-exporter",
        "postgres-exporter"
    )
    
    foreach ($service in $monitoringServices) {
        Write-MonitorLog "Starting $service..." "Yellow" "⚡"
        docker-compose -f "../docker-compose.prod.yml" up -d $service 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-MonitorLog "✅ $service started successfully" "Green" "✅"
        } else {
            Write-MonitorLog "❌ Failed to start $service" "Red" "❌"
        }
        Start-Sleep -Seconds 2
    }
    
    # Wait for services to be healthy
    Write-MonitorLog "⏳ Waiting for services to be ready..." "Blue" "⏳"
    Start-Sleep -Seconds 15
    
    # Verify deployment
    $healthChecks = @{
        "Prometheus" = "http://localhost:9090/-/ready"
        "AlertManager" = "http://localhost:9093/-/ready"
        "Grafana" = "http://localhost:3000/api/health"
        "Node Exporter" = "http://localhost:9100/metrics"
        "cAdvisor" = "http://localhost:8080/healthz"
    }
    
    Write-MonitorLog "" 
    Write-MonitorLog "📊 Service Health Check:" "Cyan" "📊"
    foreach ($service in $healthChecks.Keys) {
        try {
            $response = Invoke-WebRequest -Uri $healthChecks[$service] -TimeoutSec 5 -UseBasicParsing 2>$null
            if ($response.StatusCode -eq 200) {
                Write-MonitorLog "✅ $service is healthy" "Green" "✅"
            } else {
                Write-MonitorLog "⚠️  $service responded with status: $($response.StatusCode)" "Yellow" "⚠️"
            }
        } catch {
            Write-MonitorLog "❌ $service is not responding" "Red" "❌"
        }
    }
    
    Write-MonitorLog "" 
    Write-MonitorLog "🎉 Monitoring stack deployment completed!" "Green" "🎉"
    Write-MonitorLog "📊 Prometheus: http://localhost:9090" "White" "📊"
    Write-MonitorLog "📈 Grafana: http://localhost:3000 (admin/admin)" "White" "📈"
    Write-MonitorLog "🚨 AlertManager: http://localhost:9093" "White" "🚨"
    
    return $true
}

function Get-MonitoringStatus {
    Write-MonitorLog "QuantLib Pro Monitoring Status" "Cyan" "📊"
    Write-MonitorLog "════════════════════════════════" "Gray"
    
    # Check running containers
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=quantlib-"
    if ($containers) {
        Write-MonitorLog "" 
        Write-MonitorLog "🔧 Running Services:" "Yellow" "🔧"
        $containers | ForEach-Object {
            if ($_ -match "quantlib-(prometheus|grafana|alertmanager|node-exporter|cadvisor|redis-exporter|postgres-exporter)") {
                Write-MonitorLog "  ✅ $_" "Green" "✅"
            }
        }
    }
    
    # Check metrics endpoints
    Write-MonitorLog "" 
    Write-MonitorLog "📡 Metrics Endpoints:" "Yellow" "📡"
    
    $endpoints = @{
        "QuantLib App" = "http://localhost:8501/metrics"
        "Prometheus" = "http://localhost:9090/metrics"
        "Node Exporter" = "http://localhost:9100/metrics"
        "Redis Exporter" = "http://localhost:9121/metrics"
        "PostgreSQL Exporter" = "http://localhost:9187/metrics"
    }
    
    foreach ($endpoint in $endpoints.Keys) {
        try {
            $response = Invoke-WebRequest -Uri $endpoints[$endpoint] -TimeoutSec 3 -UseBasicParsing 2>$null
            $responseSize = $response.Content.Length
            Write-MonitorLog "  ✅ $endpoint ($responseSize bytes)" "Green" "✅"
        } catch {
            Write-MonitorLog "  ❌ $endpoint (not responding)" "Red" "❌"
        }
    }
    
    # Check alert status
    try {
        $alerts = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/alerts" -TimeoutSec 5 2>$null
        $activeAlerts = $alerts.data | Where-Object { $_.state -eq "firing" }
        
        Write-MonitorLog ""
        Write-MonitorLog "Active Alerts" "Yellow" "🚨"
        if ($activeAlerts) {
            $activeAlerts | ForEach-Object {
                $alertName = $_.labels.alertname
                $severity = $_.labels.severity
                Write-MonitorLog "  🔥 $alertName ($severity)" "Red" "🔥"
            }
        } else {
            Write-MonitorLog "  ✅ No active alerts" "Green" "✅"
        }
    } catch {
        Write-MonitorLog "  ⚠️  Could not fetch alert status" "Yellow" "⚠️"
    }
}

function Get-ServiceLogs {
    param([string]$ServiceName)
    
    if ($ServiceName) {
        Write-MonitorLog "Logs for quantlib-$ServiceName" "Cyan" "📋"
        docker logs --tail 50 "quantlib-$ServiceName" 2>$null
    } else {
        Write-MonitorLog "Recent logs from all monitoring services" "Cyan" "📋"
        
        $services = @("prometheus", "grafana", "alertmanager")
        foreach ($service in $services) {
            Write-MonitorLog "" 
            Write-MonitorLog "─── $service ───" "Yellow" "📋"
            docker logs --tail 10 "quantlib-$service" 2>$null
        }
    }
}

function Reset-MonitoringStack {
    Write-MonitorLog "🔄 Resetting monitoring stack..." "Yellow" "🔄"
    
    $services = @(
        "quantlib-prometheus",
        "quantlib-alertmanager", 
        "quantlib-grafana",
        "quantlib-node-exporter",
        "quantlib-cadvisor",
        "quantlib-redis-exporter",
        "quantlib-postgres-exporter"
    )
    
    # Stop services
    foreach ($service in $services) {
        Write-MonitorLog "Stopping $service..." "Gray" "⏹️"
        docker stop $service 2>$null
        docker rm $service 2>$null
    }
    
    # Remove volumes (optional - prompts user)
    Write-Host "Do you want to remove monitoring data volumes? (y/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "y" -or $response -eq "Y") {
        Write-MonitorLog "🗑️  Removing monitoring volumes..." "Red" "🗑️"
        docker volume rm `
            advancedquant_prometheus-data `
            advancedquant_grafana-data `
            advancedquant_alertmanager-data 2>$null
    }
    
    Write-MonitorLog "✅ Monitoring stack reset completed" "Green" "✅"
}

function Configure-Monitoring {
    Write-MonitorLog "⚙️  Configuring monitoring settings..." "Cyan" "⚙️"
    
    # Check if secrets are configured
    if (Test-Path "../.env.production") {
        Write-MonitorLog "✅ Production secrets found" "Green" "✅"
        
        # Extract Grafana password from production secrets
        $envContent = Get-Content "../.env.production"
        $grafanaPassword = ($envContent | Where-Object { $_ -match "^GRAFANA_PASSWORD=" }) -replace "GRAFANA_PASSWORD=", ""
        
        if ($grafanaPassword) {
            Write-MonitorLog "✅ Grafana admin password configured" "Green" "✅"
        } else {
            Write-MonitorLog "⚠️  No Grafana password found in production secrets" "Yellow" "⚠️"
        }
    }
    
    # Create dashboard provisioning config
    $dashboardConfig = @"
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: 'QuantLib Pro'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
"@
    
    $configPath = "../monitoring/grafana/dashboards/dashboard-config.yml"
    Set-Content -Path $configPath -Value $dashboardConfig
    Write-MonitorLog "✅ Dashboard provisioning configured" "Green" "✅"
    
    Write-MonitorLog "⚙️  Configuration completed!" "Green" "⚙️"
}

# Main execution
switch ($Action.ToLower()) {
    "deploy" {
        Deploy-MonitoringStack
    }
    
    "status" {
        Get-MonitoringStatus
    }
    
    "logs" {
        Get-ServiceLogs -ServiceName $Service
    }
    
    "reset" {
        Reset-MonitoringStack
    }
    
    "configure" {
        Configure-Monitoring
    }
    
    default {
        Write-MonitorLog "📊 QuantLib Pro - Production Monitoring Manager" "Cyan" "📊"
        Write-MonitorLog "═══════════════════════════════════════════════" "Gray"
        Write-MonitorLog ""
        Write-MonitorLog "Commands:" "Yellow" "📖"
        Write-MonitorLog "  -Action deploy      Deploy full monitoring stack" "White"
        Write-MonitorLog "  -Action status      Show monitoring system status" "White"
        Write-MonitorLog "  -Action logs        Show logs (-Service <name> for specific service)" "White"
        Write-MonitorLog "  -Action reset       Reset/remove monitoring stack" "White"
        Write-MonitorLog "  -Action configure   Configure monitoring settings" "White"
        Write-MonitorLog ""
        Write-MonitorLog "Examples:" "Green" "💡"
        Write-MonitorLog "  .\monitoring-manager.ps1 -Action deploy" "White"
        Write-MonitorLog "  .\monitoring-manager.ps1 -Action status" "White" 
        Write-MonitorLog "  .\monitoring-manager.ps1 -Action logs -Service prometheus" "White"
        Write-MonitorLog ""
        Write-MonitorLog "Monitoring Stack:" "Green" "🛡️"
        Write-MonitorLog "  • Prometheus - Metrics collection & alerting" "White" "📊"
        Write-MonitorLog "  • Grafana - Dashboards & visualization" "White" "📈"
        Write-MonitorLog "  • AlertManager - Alert routing & notifications" "White" "🚨"
        Write-MonitorLog "  • Node Exporter - System metrics" "White" "🖥️"
        Write-MonitorLog "  • cAdvisor - Container metrics" "White" "🐳"
        Write-MonitorLog "  • Database & Redis exporters" "White" "🗄️"
    }
}