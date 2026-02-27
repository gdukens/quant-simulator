# Production Performance Optimization Script for QuantLib Pro
# This script starts the API with optimized settings for production performance

param(
    [string]$Mode = "production",
    [int]$Port = 8002,
    [int]$Workers = 4
)

Write-Host "🚀 Starting QuantLib Pro with Performance Optimizations" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Gray

# Kill any existing processes on the target port
$existingProcess = Get-Process | Where-Object { $_.ProcessName -match "uvicorn|python" } | ForEach-Object {
    $connections = netstat -ano | Where-Object { $_ -match ":$Port " -and $_ -match $_.Id }
    if ($connections) { $_ }
} | Select-Object -First 1

if ($existingProcess) {
    Write-Host "⚠️  Stopping existing process on port $Port..." -ForegroundColor Yellow
    Stop-Process -Id $existingProcess.Id -Force
    Start-Sleep -Seconds 2
}

Write-Host "🔧 Performance Configuration:" -ForegroundColor Blue
Write-Host "  • Mode: $Mode" -ForegroundColor White
Write-Host "  • Port: $Port" -ForegroundColor White  
Write-Host "  • Workers: $Workers" -ForegroundColor White
Write-Host "  • Event Loop: Auto-optimized" -ForegroundColor White
Write-Host "  • HTTP Implementation: Auto-optimized" -ForegroundColor White
Write-Host "  • Connection Backlog: 2048" -ForegroundColor White
Write-Host "  • Keep-Alive Timeout: 65s" -ForegroundColor White
Write-Host ""

try {
    if ($Mode -eq "production") {
        Write-Host "🏭 Starting PRODUCTION mode with performance optimizations..." -ForegroundColor Green
        
        # Production configuration with optimal performance settings
        uvicorn main_api:app `
            --host 0.0.0.0 `
            --port $Port `
            --workers $Workers `
            --loop auto `
            --http auto `
            --log-level info `
            --no-access-log `
            --backlog 2048 `
            --limit-max-requests 10000 `
            --limit-concurrency 100 `
            --timeout-keep-alive 65 `
            --timeout-graceful-shutdown 30
            
    } elseif ($Mode -eq "development") {
        Write-Host "🔧 Starting DEVELOPMENT mode with hot reload..." -ForegroundColor Yellow
        
        # Development configuration with hot reload
        uvicorn main_api:app `
            --host 0.0.0.0 `
            --port $Port `
            --reload `
            --loop auto `
            --http auto `
            --log-level debug `
            --access-log `
            --reload-dir . `
            --reload-include="*.py"
            
    } else {
        Write-Host "🧪 Starting PERFORMANCE TEST mode..." -ForegroundColor Magenta
        
        # Performance testing configuration
        uvicorn main_api:app `
            --host 0.0.0.0 `
            --port $Port `
            --workers 2 `
            --loop auto `
            --http auto `
            --log-level warning `
            --no-access-log `
            --backlog 4096 `
            --limit-concurrency 200 `
            --timeout-keep-alive 120
    }
    
} catch {
    Write-Host "❌ Failed to start API server: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ API Server started successfully!" -ForegroundColor Green
Write-Host "📊 Access documentation: http://localhost:$Port/docs" -ForegroundColor Blue
Write-Host "❤️  Health check: http://localhost:$Port/health" -ForegroundColor Blue  
Write-Host "📈 Performance stats: http://localhost:$Port/performance/stats" -ForegroundColor Blue