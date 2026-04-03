# API Performance Benchmark Script for QuantLib Pro
# Tests response times and throughput for production readiness

param(
    [string]$BaseUrl = "http://localhost:8002",
    [int]$Requests = 10,
    [int]$Concurrent = 3
)

Write-Host " QuantLib Pro API Performance Benchmark" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Gray

# Test endpoints with expected performance targets
$endpoints = @(
    @{ Path = "/health"; Target = 100; Description = "Health Check" },
    @{ Path = "/"; Target = 200; Description = "API Root" },
    @{ Path = "/api/v1/macro/regime"; Target = 500; Description = "Macro Analysis" },
    @{ Path = "/api"; Target = 150; Description = "API Info" }
)

$results = @()

foreach ($endpoint in $endpoints) {
    Write-Host " Testing: $($endpoint.Description)" -ForegroundColor Blue
    Write-Host "   URL: $BaseUrl$($endpoint.Path)" -ForegroundColor Gray
    Write-Host "   Target: <$($endpoint.Target)ms" -ForegroundColor Gray
    
    $times = @()
    $successful = 0
    
    for ($i = 1; $i -le $Requests; $i++) {
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            
            $response = Invoke-RestMethod -Uri "$BaseUrl$($endpoint.Path)" -Method GET -TimeoutSec 5 -ErrorAction Stop
            
            $stopwatch.Stop()
            $responseTime = $stopwatch.ElapsedMilliseconds
            $times += $responseTime
            $successful++
            
            $status = if ($responseTime -le $endpoint.Target) { "" } else { "" }
            Write-Host "   Request $i`: ${responseTime}ms $status" -ForegroundColor $(if ($responseTime -le $endpoint.Target) { "Green" } else { "Red" })
            
        } catch {
            Write-Host "   Request $i`: ERROR - $($_.Exception.Message)" -ForegroundColor Red
            $times += 9999
        }
        
        Start-Sleep -Milliseconds 100  # Brief pause between requests
    }
    
    if ($times.Count -gt 0) {
        $validTimes = $times | Where-Object { $_ -lt 9999 }
        
        if ($validTimes.Count -gt 0) {
            $avgTime = [math]::Round(($validTimes | Measure-Object -Average).Average, 1)
            $minTime = ($validTimes | Measure-Object -Minimum).Minimum  
            $maxTime = ($validTimes | Measure-Object -Maximum).Maximum
            $successRate = [math]::Round(($successful / $Requests) * 100, 1)
            
            $performance = if ($avgTime -le $endpoint.Target) { " PASS" } else { " FAIL" }
            
            Write-Host "   Results:" -ForegroundColor Yellow
            Write-Host "     Average: ${avgTime}ms" -ForegroundColor White
            Write-Host "     Range: ${minTime}ms - ${maxTime}ms" -ForegroundColor White  
            Write-Host "     Success Rate: ${successRate}%" -ForegroundColor White
            Write-Host "     Performance: $performance" -ForegroundColor $(if ($avgTime -le $endpoint.Target) { "Green" } else { "Red" })
            
            $results += @{
                Endpoint = $endpoint.Description
                Path = $endpoint.Path
                AverageTime = $avgTime
                Target = $endpoint.Target
                MinTime = $minTime
                MaxTime = $maxTime
                SuccessRate = $successRate
                Status = if ($avgTime -le $endpoint.Target) { "PASS" } else { "FAIL" }
            }
        }
    }
    
    Write-Host ""
}

# Overall Performance Summary
Write-Host " PERFORMANCE SUMMARY" -ForegroundColor Cyan
Write-Host "══════════════════════" -ForegroundColor Gray

$passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$totalCount = $results.Count
$overallAvg = [math]::Round(($results | ForEach-Object { $_.AverageTime } | Measure-Object -Average).Average, 1)

Write-Host "Overall Results:" -ForegroundColor Yellow
Write-Host "  Tests Passed: $passCount/$totalCount" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Red" })
Write-Host "  Average Response Time: ${overallAvg}ms" -ForegroundColor $(if ($overallAvg -lt 500) { "Green" } else { "Red" })  
Write-Host "  Production Target: <500ms" -ForegroundColor Gray

$productionReady = ($passCount -eq $totalCount) -and ($overallAvg -lt 500)
$status = if ($productionReady) { " PRODUCTION READY" } else { " NEEDS OPTIMIZATION" }

Write-Host ""
Write-Host "Production Status: $status" -ForegroundColor $(if ($productionReady) { "Green" } else { "Red" })

if (-not $productionReady) {
    Write-Host ""
    Write-Host " Optimization Recommendations:" -ForegroundColor Yellow
    Write-Host "  • Enable Redis caching for data endpoints" -ForegroundColor White
    Write-Host "  • Increase Uvicorn worker processes" -ForegroundColor White  
    Write-Host "  • Optimize database connection pooling" -ForegroundColor White
    Write-Host "  • Enable response compression (GZip)" -ForegroundColor White
}

# Detailed Results Table
Write-Host ""
Write-Host " DETAILED RESULTS" -ForegroundColor Cyan
Write-Host "═══════════════════" -ForegroundColor Gray

$results | ForEach-Object {
    Write-Host "$($_.Endpoint):" -ForegroundColor Blue
    Write-Host "  Path: $($_.Path)" -ForegroundColor Gray
    Write-Host "  Performance: $($_.AverageTime)ms (Target: $($_.Target)ms)" -ForegroundColor White
    Write-Host "  Status: $($_.Status)" -ForegroundColor $(if ($_.Status -eq "PASS") { "Green" } else { "Red" })
    Write-Host ""
}

return $productionReady