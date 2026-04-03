# QuantLib Pro - Safe Docker Network Management
# This script provides safe alternatives to `docker network prune -f`

param(
    [switch]$Restore,
    [switch]$SafeCleanup,
    [switch]$Status
)

# Networks to preserve (never delete these)
$PRESERVE_NETWORKS = @(
    "supabase_network_sxdwyjyydsnvcbcrsyml",
    "abtesting_default",
    "quantlib-pro-network",
    "quantlib-network",
    "bridge",
    "host",
    "none"
)

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host " $Message" -ForegroundColor $Color
}

function Get-NetworkStatus {
    Write-Status "Docker Network Status:" "Cyan"
    Write-Status "───────────────────────" "Gray"
    
    $networks = docker network ls --format "table {{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}"
    Write-Host $networks
    
    Write-Status "`nPreserved Networks:" "Yellow"
    foreach ($network in $PRESERVE_NETWORKS) {
        $exists = docker network ls --filter "name=$network" --format "{{.Name}}" 2>$null
        if ($exists) {
            Write-Status " $network (exists)" "Green"
        } else {
            Write-Status " $network (missing)" "Red"
        }
    }
}

function Restore-Networks {
    Write-Status "Restoring missing networks..." "Yellow"
    
    # Restore Supabase network
    $supabase = docker network ls --filter "name=supabase_network_sxdwyjyydsnvcbcrsyml" --format "{{.Name}}" 2>$null
    if (-not $supabase) {
        Write-Status "Creating Supabase network..." "Blue"
        docker network create `
            --driver bridge `
            --subnet 172.22.0.0/16 `
            --gateway 172.22.0.1 `
            supabase_network_sxdwyjyydsnvcbcrsyml
        Write-Status " Supabase network created" "Green"
    }
    
    # Restore A/B testing network  
    $abtesting = docker network ls --filter "name=abtesting_default" --format "{{.Name}}" 2>$null
    if (-not $abtesting) {
        Write-Status "Creating A/B testing network..." "Blue"
        docker network create `
            --driver bridge `
            --subnet 172.23.0.0/16 `
            --gateway 172.23.0.1 `
            abtesting_default
        Write-Status " A/B testing network created" "Green"
    }
}

function Safe-NetworkCleanup {
    Write-Status "Performing safe network cleanup..." "Yellow"
    
    # Get all networks
    $allNetworks = docker network ls --format "{{.Name}}" | Where-Object { $_ -notin $PRESERVE_NETWORKS }
    
    if ($allNetworks.Count -eq 0) {
        Write-Status "No networks to clean up" "Green"
        return
    }
    
    Write-Status "Networks that can be safely removed:" "Cyan"
    foreach ($network in $allNetworks) {
        # Check if network is in use
        $containers = docker network inspect $network --format "{{range .Containers}}{{.Name}} {{end}}" 2>$null
        if (-not $containers -or $containers.Trim() -eq "") {
            Write-Status "  $network (unused)" "Gray"
            docker network rm $network 2>$null
        } else {
            Write-Status "  $network (in use by: $containers)" "Yellow"
        }
    }
}

# Main execution
switch ($true) {
    $Status { Get-NetworkStatus }
    $Restore { Restore-Networks; Get-NetworkStatus }
    $SafeCleanup { Safe-NetworkCleanup; Get-NetworkStatus }
    default {
        Write-Status "Docker Network Manager for QuantLib Pro" "Cyan"
        Write-Status "=======================================" "Gray"
        Write-Status ""
        Write-Status "Usage:" "Yellow"
        Write-Status "  -Status         Show current network status"
        Write-Status "  -Restore        Restore missing preserved networks"
        Write-Status "  -SafeCleanup    Safely remove unused networks (preserves critical ones)"
        Write-Status ""
        Write-Status "Examples:" "Green"
        Write-Status "  .\network-management.ps1 -Status"
        Write-Status "  .\network-management.ps1 -Restore"
        Write-Status "  .\network-management.ps1 -SafeCleanup"
    }
}