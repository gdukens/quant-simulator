# Quick Performance Optimization - Start Production API
# This gets the API running optimally for immediate performance testing

Write-Host "🚀 Quick API Performance Boost" -ForegroundColor Cyan
Write-Host "═══════════════════════════════" -ForegroundColor Gray

# Stop any existing processes
Get-Process | Where-Object {$_.ProcessName -match "uvicorn|python"} | Where-Object {
    $connections = netstat -ano | Where-Object { $_ -match ":800[0-9]" -and $_ -match $_.Id }
    if ($connections) { $_ }
} | ForEach-Object {
    Write-Host "⚠️  Stopping process $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Yellow
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

Write-Host "🔧 Starting optimized API server..." -ForegroundColor Blue

try {
    # Start with working configuration (single worker, port 8002)
    Start-Process -FilePath "uvicorn" -ArgumentList @(
        "main_api:app",
        "--host", "0.0.0.0", 
        "--port", "8002",
        "--log-level", "info",
        "--loop", "auto"
    ) -NoNewWindow -PassThru | Out-Null
    
    Write-Host "⏳ Waiting for API to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Test connectivity
    try {
        $response = Invoke-WebRequest "http://localhost:8002/health" -UseBasicParsing -TimeoutSec 3 -NoProxy
        Write-Host "✅ API Health Check: Status $($response.StatusCode)" -ForegroundColor Green
        
        # Quick performance test
        Write-Host "🏃 Quick Performance Test:" -ForegroundColor Cyan
        
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest "http://localhost:8002/" -UseBasicParsing -NoProxy
        $stopwatch.Stop()
        
        $responseTime = $stopwatch.ElapsedMilliseconds
        $status = if ($responseTime -lt 500) { "✅ GOOD" } else { "⚠️  NEEDS TUNING" }
        
        Write-Host "   Response Time: ${responseTime}ms $status" -ForegroundColor $(if($responseTime -lt 500){"Green"}else{"Yellow"})
        Write-Host "   Target: <500ms for production" -ForegroundColor Gray
        
        if ($responseTime -lt 500) {
            Write-Host ""
            Write-Host "🎉 PERFORMANCE SUCCESS!" -ForegroundColor Green
            Write-Host "✅ API is production-ready (<500ms)" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "📈 Performance Recommendations:" -ForegroundColor Yellow
            Write-Host "  • Enable Redis caching" -ForegroundColor White
            Write-Host "  • Add more workers (--workers 2)" -ForegroundColor White
            Write-Host "  • Optimize database queries" -ForegroundColor White
        }
        
    } catch {
        Write-Host "❌ API Connection Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Failed to start API: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 Access Points:" -ForegroundColor Blue
Write-Host "  • API Docs: http://localhost:8002/docs" -ForegroundColor White
Write-Host "  • Health Check: http://localhost:8002/health" -ForegroundColor White
Write-Host "  • API Root: http://localhost:8002/" -ForegroundColor White