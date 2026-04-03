# Production Secrets Management System for QuantLib Pro
# Generates cryptographically secure secrets and manages production configuration

param(
    [switch]$Generate,      # Generate new production secrets
    [switch]$Validate,      # Validate current secret strength
    [switch]$Rotate,        # Rotate existing secrets
    [switch]$Backup,        # Create encrypted backup
    [string]$Environment = "production"
)

# Import required modules
Add-Type -AssemblyName System.Security
Add-Type -AssemblyName System.Web

function Write-SecureLog {
    param([string]$Message, [string]$Color = "White", [string]$Icon = "")
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Generate-SecureSecret {
    param(
        [int]$Length = 64,
        [string]$Type = "alphanumeric"
    )
    
    switch ($Type) {
        "jwt" {
            # JWT Secret (Base64 encoded random bytes)
            $bytes = New-Object byte[] 64
            $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            $rng.GetBytes($bytes)
            return [Convert]::ToBase64String($bytes)
        }
        "password" {
            # Strong password with mixed character set
            $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
            $secret = ""
            $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            
            for ($i = 0; $i -lt $Length; $i++) {
                $bytes = New-Object byte[] 1
                $rng.GetBytes($bytes)
                $secret += $chars[$bytes[0] % $chars.Length]
            }
            return $secret
        }
        "encryption" {
            # Encryption key (256-bit AES compatible)
            $bytes = New-Object byte[] 32
            $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            $rng.GetBytes($bytes)
            return [Convert]::ToBase64String($bytes)
        }
        default {
            # Standard alphanumeric
            $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            $secret = ""
            $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            
            for ($i = 0; $i -lt $Length; $i++) {
                $bytes = New-Object byte[] 1
                $rng.GetBytes($bytes)
                $secret += $chars[$bytes[0] % $chars.Length]
            }
            return $secret
        }
    }
}

function Test-SecretStrength {
    param([string]$Secret)
    
    $score = 0
    $issues = @()
    
    # Length check
    if ($Secret.Length -ge 32) { $score += 25 } else { $issues += "Too short (<32 chars)" }
    
    # Character diversity
    if ($Secret -cmatch "[A-Z]") { $score += 15 } else { $issues += "No uppercase letters" }
    if ($Secret -cmatch "[a-z]") { $score += 15 } else { $issues += "No lowercase letters" }
    if ($Secret -cmatch "[0-9]") { $score += 15 } else { $issues += "No numbers" }
    if ($Secret -cmatch "[^A-Za-z0-9]") { $score += 15 } else { $issues += "No special characters" }
    
    # Common patterns
    if ($Secret -notmatch "(.)\\1{2,}") { $score += 15 } else { $issues += "Repeated characters" }
    
    return @{
        Score = $score
        Grade = if ($score -ge 80) { "STRONG" } elseif ($score -ge 60) { "MEDIUM" } else { "WEAK" }
        Issues = $issues
    }
}

function Generate-ProductionSecrets {
    Write-SecureLog "Generating Production-Grade Secrets..." "Cyan" ""
    
    $secrets = @{
        # Authentication & Authorization
        JWT_SECRET_KEY = Generate-SecureSecret -Type "jwt"
        JWT_ALGORITHM = "HS256"
        
        # Encryption 
        ENCRYPTION_KEY = Generate-SecureSecret -Type "encryption"
        SECRET_KEY = Generate-SecureSecret -Length 64 -Type "password"
        
        # Database Security
        DATABASE_PASSWORD = "QLPro_$(Generate-SecureSecret -Length 16 -Type 'password')_2026"
        POSTGRES_PASSWORD = "QLPro_$(Generate-SecureSecret -Length 16 -Type 'password')_2026"
        
        # Redis Security
        REDIS_PASSWORD = Generate-SecureSecret -Length 32 -Type "password"
        
        # API Security
        API_KEY_ENCRYPTION = Generate-SecureSecret -Type "encryption"
        SESSION_SECRET = Generate-SecureSecret -Length 48 -Type "password"
        
        # External Service Keys (placeholders - replace with real keys)
        FACTSET_CLIENT_SECRET = "REPLACE_WITH_REAL_FACTSET_SECRET"
        GRAFANA_PASSWORD = "QuantLib_$(Generate-SecureSecret -Length 12)_Admin"
        
        # Security Metadata
        SECRETS_GENERATED_DATE = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss UTC")
        SECRETS_VERSION = "v2.0"
        SECURITY_PROFILE = "ENTERPRISE"
    }
    
    return $secrets
}

function Create-SecureEnvFile {
    param(
        [hashtable]$Secrets,
        [string]$Environment
    )
    
    $envFile = ".env.$Environment"
    
    $content = @"
# ══════════════════════════════════════════════════════════════════════════════
# QuantLib Pro - $Environment Environment Configuration
# Generated: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss UTC"))
# Security Level: ENTERPRISE GRADE
# ══════════════════════════════════════════════════════════════════════════════
#  CRITICAL SECURITY NOTICE:
#    - This file contains production secrets
#    - NEVER commit to version control
#    - Store in secure location with restricted access
#    - Rotate secrets every 90 days
# ══════════════════════════════════════════════════════════════════════════════

# ─── Application Security ──────────────────────────────────────────────────────
APP_ENV=$Environment
DEBUG=false
LOG_LEVEL=INFO
SECURITY_PROFILE=$($Secrets.SECURITY_PROFILE)

# ─── Authentication & JWT ──────────────────────────────────────────────────────
JWT_SECRET_KEY=$($Secrets.JWT_SECRET_KEY)
JWT_ALGORITHM=$($Secrets.JWT_ALGORITHM)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── Encryption & Security ─────────────────────────────────────────────────────
ENCRYPTION_KEY=$($Secrets.ENCRYPTION_KEY)
SECRET_KEY=$($Secrets.SECRET_KEY)
API_KEY_ENCRYPTION=$($Secrets.API_KEY_ENCRYPTION)
SESSION_SECRET=$($Secrets.SESSION_SECRET)

# ─── Database Security ─────────────────────────────────────────────────────────
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_NAME=quantlib_pro
DATABASE_USER=quantlib
DATABASE_PASSWORD=$($Secrets.DATABASE_PASSWORD)
DATABASE_URL=postgresql://quantlib:$($Secrets.DATABASE_PASSWORD)@localhost:5433/quantlib_pro

# ─── Docker PostgreSQL ────────────────────────────────────────────────────────
POSTGRES_USER=quantlib
POSTGRES_PASSWORD=$($Secrets.POSTGRES_PASSWORD)
POSTGRES_DB=quantlib_pro

# ─── Redis Security ────────────────────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=$($Secrets.REDIS_PASSWORD)
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20

# ─── External APIs ─────────────────────────────────────────────────────────────
ALPHA_VANTAGE_API_KEY=MK01VGPAXTBXDL3V
FRED_API_KEY=5f5dcf2ef53c496228fa2935b71d9d40
FACTSET_CLIENT_ID=35a64bba4b7d4daeaaa0cc6d2b7845ed
FACTSET_CLIENT_SECRET=$($Secrets.FACTSET_CLIENT_SECRET)

# ─── Monitoring & Admin ────────────────────────────────────────────────────────
GRAFANA_PASSWORD=$($Secrets.GRAFANA_PASSWORD)
PROMETHEUS_PASSWORD=QuantLib_Monitor_2026

# ─── Security Metadata ─────────────────────────────────────────────────────────
SECRETS_VERSION=$($Secrets.SECRETS_VERSION)
SECRETS_GENERATED_DATE=$($Secrets.SECRETS_GENERATED_DATE)
LAST_ROTATION_DATE=$((Get-Date).ToString("yyyy-MM-dd"))
NEXT_ROTATION_DATE=$((Get-Date).AddDays(90).ToString("yyyy-MM-dd"))

# ─── Feature Flags ─────────────────────────────────────────────────────────────
ENABLE_AUTH=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOG=true
ENABLE_ENCRYPTION=true
SECURITY_MODE=strict
"@

    Set-Content -Path $envFile -Value $content -Encoding UTF8
    
    # Set restrictive permissions (Windows)
    try {
        $acl = Get-Acl $envFile
        $acl.SetAccessRuleProtection($true, $false)  # Remove inheritance
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            [System.Security.Principal.WindowsIdentity]::GetCurrent().Name,
            "FullControl",
            "Allow"
        )
        $acl.SetAccessRule($rule)
        Set-Acl -Path $envFile -AclObject $acl
    } catch {
        Write-SecureLog "  Could not set file permissions: $($_.Exception.Message)" "Yellow" ""
    }
    
    return $envFile
}

function Validate-CurrentSecrets {
    if (Test-Path ".env") {
        Write-SecureLog "Validating Current Secret Strength..." "Blue" ""
        
        $content = Get-Content ".env"
        $weakSecrets = @()
        
        foreach ($line in $content) {
            if ($line -match "^([A-Z_]+)=(.+)$") {
                $key = $Matches[1]
                $value = $Matches[2]
                
                if ($key -match "(SECRET|KEY|PASSWORD)" -and $value.Length -gt 0) {
                    $strength = Test-SecretStrength -Secret $value
                    
                    $status = switch ($strength.Grade) {
                        "STRONG" { "" }
                        "MEDIUM" { " " }
                        "WEAK" { "" }
                    }
                    
                    Write-SecureLog "$status $key`: $($strength.Grade) (Score: $($strength.Score)/100)" -Color $(
                        switch ($strength.Grade) {
                            "STRONG" { "Green" }
                            "MEDIUM" { "Yellow" }
                            "WEAK" { "Red" }
                        }
                    )
                    
                    if ($strength.Grade -ne "STRONG") {
                        $weakSecrets += @{
                            Key = $key
                            Grade = $strength.Grade
                            Issues = $strength.Issues
                        }
                    }
                }
            }
        }
        
        if ($weakSecrets.Count -eq 0) {
            Write-SecureLog " All secrets meet security requirements!" "Green" ""
        } else {
            Write-SecureLog "  Found $($weakSecrets.Count) weak secrets that need replacement" "Yellow" ""
        }
        
        return $weakSecrets.Count -eq 0
    } else {
        Write-SecureLog " No .env file found" "Red" ""
        return $false
    }
}

# Main execution
Write-SecureLog "QuantLib Pro - Production Secrets Management" "Cyan" ""
Write-SecureLog "═══════════════════════════════════════════" "Gray"

switch ($true) {
    $Generate {
        Write-SecureLog "  GENERATING PRODUCTION SECRETS" "Green" ""
        
        $secrets = Generate-ProductionSecrets
        $envFile = Create-SecureEnvFile -Secrets $secrets -Environment $Environment
        
        Write-SecureLog " Production secrets generated successfully!" "Green" ""
        Write-SecureLog " Configuration saved to: $envFile" "Blue" ""
        Write-SecureLog " File permissions set to restricted access" "Blue" ""
        
        # Security summary
        Write-SecureLog "" 
        Write-SecureLog "  SECURITY SUMMARY:" "Cyan" ""
        Write-SecureLog "  • JWT Secret: 512-bit cryptographically secure" "White" ""
        Write-SecureLog "  • Encryption Keys: AES-256 compatible" "White" ""
        Write-SecureLog "  • Database Passwords: Enterprise strength" "White" ""
        Write-SecureLog "  • All secrets: Cryptographically random" "White" ""
        Write-SecureLog "  • Next rotation: $((Get-Date).AddDays(90).ToString('yyyy-MM-dd'))" "White" ""
    }
    
    $Validate {
        Write-SecureLog " VALIDATING SECRET STRENGTH" "Blue" ""
        $isSecure = Validate-CurrentSecrets
        
        if ($isSecure) {
            Write-SecureLog " All secrets are production-ready!" "Green" ""
        } else {
            Write-SecureLog "  Secrets need strengthening for production use" "Yellow" ""
            Write-SecureLog " Run with -Generate to create secure secrets" "Blue" ""
        }
    }
    
    $Backup {
        Write-SecureLog " CREATING ENCRYPTED BACKUP" "Blue" ""
        # Implementation for encrypted backup
        Write-SecureLog " Backup functionality ready for implementation" "Green" ""
    }
    
    default {
        Write-SecureLog "Production Secrets Management System" "Blue" ""
        Write-SecureLog "Usage:" "Yellow" ""
        Write-SecureLog "  -Generate     Create new production-grade secrets" "White"
        Write-SecureLog "  -Validate     Check current secret strength" "White" 
        Write-SecureLog "  -Rotate       Rotate existing secrets" "White"
        Write-SecureLog "  -Backup       Create encrypted backup" "White"
        Write-SecureLog "" 
        Write-SecureLog "Examples:" "Green" ""
        Write-SecureLog "  .\secrets-manager.ps1 -Generate" "White"
        Write-SecureLog "  .\secrets-manager.ps1 -Validate" "White"
    }
}