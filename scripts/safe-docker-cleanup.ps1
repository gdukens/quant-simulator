# Safe Docker Cleanup - Replacement for dangerous `docker network prune -f`
# This script safely cleans Docker resources while preserving critical networks

param(
    [switch]$Networks,
    [switch]$Containers,
    [switch]$Images,
    [switch]$Volumes,
    [switch]$All,
    [switch]$DryRun
)

# CRITICAL NETWORKS TO NEVER DELETE
$PRESERVE_NETWORKS = @(
    "supabase_network_sxdwyjyydsnvcbcrsyml",
    "abtesting_default",
    "quantlib-pro-network",
    "quantlib-network",
    "bridge",
    "host",
    "none"
)

function Write-SafeLog {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "🛡️")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Safe-NetworkCleanup {
    param([bool]$DryRun = $false)
    
    Write-SafeLog "SAFE Network Cleanup (Preserving Critical Networks)" "Cyan"
    Write-SafeLog "═══════════════════════════════════════════════════" "Gray"
    
    # Get all networks except preserved ones
    $allNetworks = docker network ls --format "{{.Name}}" 2>$null
    $candidateNetworks = $allNetworks | Where-Object { $_ -notin $PRESERVE_NETWORKS }
    
    if ($candidateNetworks.Count -eq 0) {
        Write-SafeLog "✅ No networks to clean up" "Green"
        return
    }
    
    foreach ($network in $candidateNetworks) {
        # Check if network is in use
        $containers = docker network inspect $network --format "{{range .Containers}}{{.Name}} {{end}}" 2>$null
        
        if (-not $containers -or $containers.Trim() -eq "") {
            if ($DryRun) {
                Write-SafeLog "🔍 Would remove unused network: $network" "Yellow" "🔍"
            } else {
                Write-SafeLog "🗑️  Removing unused network: $network" "Gray" "🗑️"
                docker network rm $network 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-SafeLog "✅ Successfully removed: $network" "Green"
                } else {
                    Write-SafeLog "❌ Failed to remove: $network" "Red"
                }
            }
        } else {
            Write-SafeLog "⚠️  Skipping in-use network: $network (containers: $($containers.Trim()))" "Yellow" "⚠️"
        }
    }
    
    Write-SafeLog "`nPRESERVED Networks (never touched):" "Green" "🛡️"
    foreach ($preserved in $PRESERVE_NETWORKS) {
        $exists = docker network ls --filter "name=$preserved" --format "{{.Name}}" 2>$null
        if ($exists) {
            Write-SafeLog "✅ $preserved" "Green" "🔒"
        }
    }
}

function Safe-ContainerCleanup {
    param([bool]$DryRun = $false)
    
    Write-SafeLog "SAFE Container Cleanup" "Cyan"
    Write-SafeLog "═════════════════════" "Gray"
    
    if ($DryRun) {
        Write-SafeLog "🔍 Dry run - would remove stopped containers:" "Yellow" "🔍"
        docker container ls -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}"
    } else {
        Write-SafeLog "🗑️  Removing stopped containers..." "Gray" "🗑️"
        docker container prune -f
        Write-SafeLog "✅ Stopped containers cleaned up" "Green"
    }
}

function Safe-ImageCleanup {
    param([bool]$DryRun = $false)
    
    Write-SafeLog "SAFE Image Cleanup" "Cyan" 
    Write-SafeLog "═════════════════" "Gray"
    
    if ($DryRun) {
        Write-SafeLog "🔍 Dry run - would remove dangling images:" "Yellow" "🔍"
        docker images --filter "dangling=true" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    } else {
        Write-SafeLog "🗑️  Removing dangling images..." "Gray" "🗑️"
        docker image prune -f
        Write-SafeLog "✅ Dangling images cleaned up" "Green"
    }
}

function Safe-VolumeCleanup {
    param([bool]$DryRun = $false)
    
    Write-SafeLog "SAFE Volume Cleanup" "Cyan"
    Write-SafeLog "══════════════════" "Gray"
    
    if ($DryRun) {
        Write-SafeLog "🔍 Dry run - would remove unused volumes:" "Yellow" "🔍"
        docker volume ls --filter "dangling=true" --format "table {{.Name}}\t{{.Driver}}"
    } else {
        Write-SafeLog "🗑️  Removing unused volumes..." "Gray" "🗑️"
        docker volume prune -f
        Write-SafeLog "✅ Unused volumes cleaned up" "Green"
    }
}

# Main execution
$isDryRun = $DryRun.IsPresent

if ($isDryRun) {
    Write-SafeLog "🔍 DRY RUN MODE - No actual changes will be made" "Yellow" "🔍"
    Write-SafeLog "═══════════════════════════════════════════════" "Gray"
}

switch ($true) {
    $Networks { Safe-NetworkCleanup -DryRun $isDryRun }
    $Containers { Safe-ContainerCleanup -DryRun $isDryRun }
    $Images { Safe-ImageCleanup -DryRun $isDryRun }
    $Volumes { Safe-VolumeCleanup -DryRun $isDryRun }
    $All { 
        Safe-ContainerCleanup -DryRun $isDryRun
        Safe-ImageCleanup -DryRun $isDryRun
        Safe-NetworkCleanup -DryRun $isDryRun
        Safe-VolumeCleanup -DryRun $isDryRun
    }
    default {
        Write-SafeLog "🛡️  SAFE Docker Cleanup - Protects Critical Networks" "Cyan" "🛡️"
        Write-SafeLog "═══════════════════════════════════════════════════════" "Gray"
        Write-SafeLog ""
        Write-SafeLog "⚠️  NEVER USE: docker network prune -f" "Red" "❌"
        Write-SafeLog "✅ INSTEAD USE: This safe cleanup script" "Green" "✅"
        Write-SafeLog ""
        Write-SafeLog "Usage:" "Yellow" "📖"
        Write-SafeLog "  -Networks     Clean unused networks (preserves critical ones)"
        Write-SafeLog "  -Containers   Clean stopped containers"
        Write-SafeLog "  -Images       Clean dangling images"
        Write-SafeLog "  -Volumes      Clean unused volumes"
        Write-SafeLog "  -All          Clean everything safely"
        Write-SafeLog "  -DryRun       Show what would be cleaned (no changes)"
        Write-SafeLog ""
        Write-SafeLog "Examples:" "Green" "💡"
        Write-SafeLog "  .\safe-docker-cleanup.ps1 -All -DryRun    # Preview all cleanup"
        Write-SafeLog "  .\safe-docker-cleanup.ps1 -Networks       # Safe network cleanup"
        Write-SafeLog "  .\safe-docker-cleanup.ps1 -All            # Full safe cleanup"
        Write-SafeLog ""
        Write-SafeLog "Protected Networks:" "Green" "🔒"
        foreach ($network in $PRESERVE_NETWORKS) {
            Write-SafeLog "  🛡️  $network" "Green" "🔒"
        }
    }
}