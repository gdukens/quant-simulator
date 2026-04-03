# Docker Secrets Management for QuantLib Pro Production
# Sets up and manages Docker Swarm secrets for secure production deployment

param(
    [string]$Action = "help",
    [switch]$Initialize,
    [switch]$Deploy,
    [switch]$Status,
    [switch]$Rotate
)

function Write-SecureLog {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Initialize-DockerSwarm {
    Write-SecureLog "Initializing Docker Swarm for secrets management..." "Cyan" ""
    
    # Check if already in swarm mode
    $swarmStatus = docker info --format "{{.Swarm.LocalNodeState}}" 2>$null
    
    if ($swarmStatus -eq "active") {
        Write-SecureLog " Docker Swarm already initialized" "Green" ""
    } else {
        Write-SecureLog " Initializing Docker Swarm..." "Yellow" ""
        docker swarm init 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-SecureLog " Docker Swarm initialized successfully" "Green" ""
        } else {
            Write-SecureLog " Failed to initialize Docker Swarm" "Red" ""
            return $false
        }
    }
    return $true
}

function Create-DockerSecrets {
    Write-SecureLog "Creating Docker secrets from production environment..." "Cyan" ""
    
    if (!(Test-Path "../.env.production")) {
        Write-SecureLog " .env.production not found. Run production-secrets.ps1 -Generate first" "Red" ""
        return $false
    }
    
    $envContent = Get-Content "../.env.production"
    $secrets = @{
        "jwt_secret" = ($envContent | Where-Object { $_ -match "^JWT_SECRET_KEY=" }) -replace "JWT_SECRET_KEY=", ""
        "encryption_key" = ($envContent | Where-Object { $_ -match "^ENCRYPTION_KEY=" }) -replace "ENCRYPTION_KEY=", ""
        "database_password" = ($envContent | Where-Object { $_ -match "^DATABASE_PASSWORD=" }) -replace "DATABASE_PASSWORD=", ""
        "api_master_key" = ($envContent | Where-Object { $_ -match "^API_MASTER_KEY=" }) -replace "API_MASTER_KEY=", ""
        "redis_password" = ($envContent | Where-Object { $_ -match "^REDIS_PASSWORD=" }) -replace "REDIS_PASSWORD=", ""
    }
    
    foreach ($secretName in $secrets.Keys) {
        $secretValue = $secrets[$secretName]
        if ($secretValue) {
            # Check if secret already exists
            $existingSecret = docker secret ls --filter "name=$secretName" --format "{{.Name}}" 2>$null
            if ($existingSecret) {
                Write-SecureLog "  Secret $secretName already exists, skipping..." "Yellow" ""
            } else {
                # Create secret
                $secretValue | docker secret create $secretName - 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-SecureLog " Created secret: $secretName" "Green" ""
                } else {
                    Write-SecureLog " Failed to create secret: $secretName" "Red" ""
                }
            }
        }
    }
    
    Write-SecureLog " Docker secrets creation completed" "Green" ""
    return $true
}

function Deploy-SecureStack {
    param([string]$StackName = "quantlibpro")
    
    Write-SecureLog "Deploying secure QuantLib Pro stack..." "Cyan" ""
    
    if (!(Test-Path "../docker-compose.secure.yml")) {
        Write-SecureLog " docker-compose.secure.yml not found" "Red" ""
        return $false
    }
    
    # Deploy stack with secrets
    docker stack deploy -c "../docker-compose.secure.yml" $StackName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-SecureLog " Secure stack deployed successfully: $StackName" "Green" ""
        
        # Wait for services to be ready
        Write-SecureLog "⏳ Waiting for services to be ready..." "Blue" "⏳"
        Start-Sleep -Seconds 10
        
        # Show service status
        docker stack services $StackName --format "table {{.Name}}\t{{.Mode}}\t{{.Replicas}}\t{{.Image}}"
        
        return $true
    } else {
        Write-SecureLog " Failed to deploy secure stack" "Red" ""
        return $false
    }
}

function Get-SecretsStatus {
    Write-SecureLog "Docker Secrets Status:" "Cyan" ""
    Write-SecureLog "════════════════════" "Gray"
    
    # Check swarm status
    $swarmStatus = docker info --format "{{.Swarm.LocalNodeState}}" 2>$null
    if ($swarmStatus -eq "active") {
        Write-SecureLog " Docker Swarm: Active" "Green" ""
    } else {
        Write-SecureLog " Docker Swarm: Not initialized" "Red" ""
        return
    }
    
    # List secrets
    Write-SecureLog "" 
    Write-SecureLog " Configured Secrets:" "Yellow" ""
    $secrets = docker secret ls --format "{{.Name}}\t{{.CreatedAt}}" 2>$null
    if ($secrets) {
        $secrets | ForEach-Object {
            $parts = $_ -split "\t"
            Write-SecureLog "   $($parts[0]) (created: $($parts[1]))" "White" ""
        }
    } else {
        Write-SecureLog "    No secrets configured" "Yellow" ""
    }
    
    # List stacks
    Write-SecureLog "" 
    Write-SecureLog " Deployed Stacks:" "Yellow" ""
    $stacks = docker stack ls --format "{{.Name}}\t{{.Services}}" 2>$null
    if ($stacks) {
        $stacks | ForEach-Object {
            $parts = $_ -split "\t"
            Write-SecureLog "   $($parts[0]) ($($parts[1]) services)" "White" ""
        }
    } else {
        Write-SecureLog "    No stacks deployed" "Yellow" ""
    }
}

function Rotate-DockerSecrets {
    param([string[]]$SecretsToRotate = @("jwt_secret", "encryption_key", "api_master_key"))
    
    Write-SecureLog "Rotating Docker secrets..." "Cyan" ""
    
    # First, rotate the secrets in .env.production
    Set-Location ".."
    .\scripts\production-secrets.ps1 -Rotate
    Set-Location "scripts"
    
    foreach ($secretName in $SecretsToRotate) {
        Write-SecureLog " Rotating secret: $secretName" "Yellow" ""
        
        # Remove old secret
        docker secret rm $secretName 2>$null
        
        # Get new value from updated .env.production
        $envContent = Get-Content "../.env.production"
        $newValue = switch ($secretName) {
            "jwt_secret" { ($envContent | Where-Object { $_ -match "^JWT_SECRET_KEY=" }) -replace "JWT_SECRET_KEY=", "" }
            "encryption_key" { ($envContent | Where-Object { $_ -match "^ENCRYPTION_KEY=" }) -replace "ENCRYPTION_KEY=", "" }
            "api_master_key" { ($envContent | Where-Object { $_ -match "^API_MASTER_KEY=" }) -replace "API_MASTER_KEY=", "" }
        }
        
        # Create new secret
        if ($newValue) {
            $newValue | docker secret create $secretName - 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-SecureLog " Rotated: $secretName" "Green" ""
            } else {
                Write-SecureLog " Failed to rotate: $secretName" "Red" ""
            }
        }
    }
    
    Write-SecureLog " Secrets rotation completed. Redeploy stack to use new secrets." "Yellow" ""
}

# Main execution
switch ($Action.ToLower()) {
    "init" {
        if (Initialize-DockerSwarm) {
            Create-DockerSecrets
        }
    }
    
    "deploy" {
        if (Initialize-DockerSwarm) {
            if (Create-DockerSecrets) {
                Deploy-SecureStack
            }
        }
    }
    
    "status" {
        Get-SecretsStatus
    }
    
    "rotate" {
        Rotate-DockerSecrets
    }
    
    default {
        Write-SecureLog " QuantLib Pro - Docker Secrets Manager" "Cyan" ""
        Write-SecureLog "══════════════════════════════════════" "Gray"
        Write-SecureLog ""
        Write-SecureLog "Commands:" "Yellow" ""
        Write-SecureLog "  -Action init      Initialize swarm & create secrets" "White"
        Write-SecureLog "  -Action deploy    Initialize, create secrets & deploy stack" "White" 
        Write-SecureLog "  -Action status    Show secrets and deployment status" "White"
        Write-SecureLog "  -Action rotate    Rotate secrets and update deployment" "White"
        Write-SecureLog ""
        Write-SecureLog "Examples:" "Green" ""
        Write-SecureLog "  .\docker-secrets.ps1 -Action init" "White"
        Write-SecureLog "  .\docker-secrets.ps1 -Action deploy" "White"
        Write-SecureLog "  .\docker-secrets.ps1 -Action status" "White"
        Write-SecureLog ""
        Write-SecureLog "Security Benefits:" "Green" ""
        Write-SecureLog "  • Secrets stored in Docker's encrypted store" "White" ""
        Write-SecureLog "  • Secrets never written to disk in containers" "White" ""
        Write-SecureLog "  • Automatic secret rotation capabilities" "White" ""
        Write-SecureLog "  • Encrypted network communication" "White" ""
        Write-SecureLog "  • Swarm-mode high availability" "White" ""
    }
}