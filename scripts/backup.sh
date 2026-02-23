#!/bin/bash

# ============================================================================
# QuantLib Pro - Automated Backup Script
# ============================================================================
# Description: Comprehensive backup solution for production data
# Usage: ./backup.sh [--full|--incremental]
# Schedule: Run daily via cron (0 2 * * *)
# ============================================================================

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DATA_DIR="${DATA_DIR:-./data}"
LOG_DIR="${LOG_DIR:-./logs}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPRESS="${BACKUP_COMPRESS:-true}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-full}"
HOSTNAME=$(hostname)

# Cloud storage configuration
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
GCS_BUCKET="${GCS_BACKUP_BUCKET:-}"
AZURE_STORAGE_CONTAINER="${AZURE_STORAGE_CONTAINER:-}"

# Database configuration (if applicable)
DB_ENABLED="${DATABASE_ENABLED:-false}"
DB_TYPE="${DATABASE_TYPE:-postgresql}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-quantlib_pro}"
DB_USER="${DATABASE_USER:-quantlib}"

# Redis configuration
REDIS_ENABLED="${REDIS_ENABLED:-true}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Email notification
ALERT_EMAIL="${ALERT_EMAIL_RECIPIENTS:-}"

# ─── Logging ────────────────────────────────────────────────────────────────
BACKUP_LOG="${LOG_DIR}/backup_${TIMESTAMP}.log"
mkdir -p "$(dirname "$BACKUP_LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$BACKUP_LOG"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$BACKUP_LOG" >&2
}

# ─── Pre-flight Checks ──────────────────────────────────────────────────────
preflight_checks() {
    log "=== Starting Preflight Checks ==="
    
    # Check if data directory exists
    if [ ! -d "$DATA_DIR" ]; then
        error "Data directory $DATA_DIR does not exist"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Check disk space (need at least 1GB free)
    AVAILABLE_SPACE=$(df -BG "$BACKUP_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 1 ]; then
        error "Insufficient disk space. Need at least 1GB, have ${AVAILABLE_SPACE}GB"
        exit 1
    fi
    
    log "✓ Preflight checks passed"
}

# ─── Backup Data Directory ──────────────────────────────────────────────────
backup_data() {
    log "=== Backing up Data Directory ==="
    
    local backup_file="$BACKUP_DIR/data_${TIMESTAMP}"
    
    if [ "$BACKUP_TYPE" = "incremental" ]; then
        # Incremental backup using --listed-incremental
        local snapshot_file="$BACKUP_DIR/data.snapshot"
        tar --create \
            --listed-incremental="$snapshot_file" \
            --file="${backup_file}.tar" \
            --directory="$(dirname "$DATA_DIR")" \
            "$(basename "$DATA_DIR")"
    else
        # Full backup
        tar --create \
            --file="${backup_file}.tar" \
            --directory="$(dirname "$DATA_DIR")" \
            "$(basename "$DATA_DIR")"
    fi
    
    # Compress if enabled
    if [ "$COMPRESS" = "true" ]; then
        log "Compressing backup..."
        gzip -f "${backup_file}.tar"
        backup_file="${backup_file}.tar.gz"
    else
        backup_file="${backup_file}.tar"
    fi
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✓ Data backup completed: $backup_file ($size)"
    
    echo "$backup_file"
}

# ─── Backup Logs ────────────────────────────────────────────────────────────
backup_logs() {
    log "=== Backing up Logs ==="
    
    if [ ! -d "$LOG_DIR" ]; then
        log "! No logs directory found, skipping"
        return
    fi
    
    local backup_file="$BACKUP_DIR/logs_${TIMESTAMP}.tar"
    
    tar --create \
        --file="$backup_file" \
        --directory="$(dirname "$LOG_DIR")" \
        "$(basename "$LOG_DIR")"
    
    if [ "$COMPRESS" = "true" ]; then
        gzip -f "$backup_file"
        backup_file="${backup_file}.gz"
    fi
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✓ Logs backup completed: $backup_file ($size)"
    
    echo "$backup_file"
}

# ─── Backup Database ────────────────────────────────────────────────────────
backup_database() {
    if [ "$DB_ENABLED" != "true" ]; then
        log "! Database backup disabled, skipping"
        return
    fi
    
    log "=== Backing up Database ==="
    
    local backup_file="$BACKUP_DIR/database_${TIMESTAMP}.sql"
    
    case "$DB_TYPE" in
        postgresql)
            log "Backing up PostgreSQL database..."
            PGPASSWORD="${DATABASE_PASSWORD:-}" pg_dump \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                -F c \
                -f "$backup_file"
            ;;
        mysql)
            log "Backing up MySQL database..."
            mysqldump \
                -h "$DB_HOST" \
                -P "$DB_PORT" \
                -u "$DB_USER" \
                -p"${DATABASE_PASSWORD:-}" \
                "$DB_NAME" \
                > "$backup_file"
            ;;
        sqlite)
            log "Backing up SQLite database..."
            local db_file="${DATABASE_FILE:-data/quantlib.db}"
            if [ -f "$db_file" ]; then
                sqlite3 "$db_file" ".backup '$backup_file'"
            fi
            ;;
        *)
            error "Unsupported database type: $DB_TYPE"
            return
            ;;
    esac
    
    if [ "$COMPRESS" = "true" ]; then
        gzip -f "$backup_file"
        backup_file="${backup_file}.gz"
    fi
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "✓ Database backup completed: $backup_file ($size)"
    
    echo "$backup_file"
}

# ─── Backup Redis ───────────────────────────────────────────────────────────
backup_redis() {
    if [ "$REDIS_ENABLED" != "true" ]; then
        log "! Redis backup disabled, skipping"
        return
    fi
    
    log "=== Backing up Redis ==="
    
    # Trigger Redis BGSAVE
    if command -v redis-cli &> /dev/null; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
        
        # Wait for save to complete
        sleep 5
        
        # Copy dump.rdb if it exists
        local redis_dump="/var/lib/redis/dump.rdb"
        if [ -f "$redis_dump" ]; then
            cp "$redis_dump" "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
            
            if [ "$COMPRESS" = "true" ]; then
                gzip -f "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
            fi
            
            log "✓ Redis backup completed"
        else
            log "! Redis dump file not found at $redis_dump"
        fi
    else
        log "! redis-cli not found, skipping Redis backup"
    fi
}

# ─── Upload to Cloud Storage ────────────────────────────────────────────────
upload_to_cloud() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    # AWS S3
    if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
        log "Uploading to S3: s3://$S3_BUCKET/$(basename "$backup_file")"
        aws s3 cp "$backup_file" "s3://$S3_BACKUP_BUCKET/" --storage-class STANDARD_IA
        log "✓ Uploaded to S3"
    fi
    
    # Google Cloud Storage
    if [ -n "$GCS_BUCKET" ] && command -v gsutil &> /dev/null; then
        log "Uploading to GCS: gs://$GCS_BUCKET/$(basename "$backup_file")"
        gsutil cp "$backup_file" "gs://$GCS_BACKUP_BUCKET/"
        log "✓ Uploaded to GCS"
    fi
    
    # Azure Blob Storage
    if [ -n "$AZURE_STORAGE_CONTAINER" ] && command -v az &> /dev/null; then
        log "Uploading to Azure: $AZURE_STORAGE_CONTAINER/$(basename "$backup_file")"
        az storage blob upload \
            --account-name "${AZURE_STORAGE_ACCOUNT:-}" \
            --container-name "$AZURE_STORAGE_CONTAINER" \
            --file "$backup_file" \
            --name "$(basename "$backup_file")"
        log "✓ Uploaded to Azure"
    fi
}

# ─── Cleanup Old Backups ────────────────────────────────────────────────────
cleanup_old_backups() {
    log "=== Cleaning up old backups (older than $RETENTION_DAYS days) ==="
    
    # Local backups
    find "$BACKUP_DIR" -name "*.tar.gz" -o -name "*.tar" -o -name "*.sql.gz" -o -name "*.sql" \
        | while read -r file; do
            if [ -f "$file" ]; then
                local age=$(find "$file" -mtime +$RETENTION_DAYS -print)
                if [ -n "$age" ]; then
                    log "Deleting old backup: $file"
                    rm -f "$file"
                fi
            fi
        done
    
    # Cloud backups
    if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
        log "Cleaning up old S3 backups..."
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        aws s3 ls "s3://$S3_BACKUP_BUCKET/" \
            | awk '{print $4}' \
            | while read -r file; do
                local file_date=$(echo "$file" | grep -oP '\d{8}' | head -1)
                if [ -n "$file_date" ]; then
                    local file_date_formatted="${file_date:0:4}-${file_date:4:2}-${file_date:6:2}"
                    if [[ "$file_date_formatted" < "$cutoff_date" ]]; then
                        log "Deleting old S3 backup: $file"
                        aws s3 rm "s3://$S3_BACKUP_BUCKET/$file"
                    fi
                fi
            done
    fi
    
    log "✓ Cleanup completed"
}

# ─── Generate Backup Manifest ───────────────────────────────────────────────
generate_manifest() {
    local manifest_file="$BACKUP_DIR/manifest_${TIMESTAMP}.txt"
    
    cat > "$manifest_file" <<EOF
QuantLib Pro Backup Manifest
=============================
Date: $(date)
Hostname: $HOSTNAME
Backup Type: $BACKUP_TYPE
Retention: $RETENTION_DAYS days

Files:
EOF
    
    find "$BACKUP_DIR" -name "*_${TIMESTAMP}.*" -type f \
        | while read -r file; do
            local size=$(du -h "$file" | cut -f1)
            local checksum=$(sha256sum "$file" | cut -d' ' -f1)
            echo "- $(basename "$file") ($size) [SHA256: $checksum]" >> "$manifest_file"
        done
    
    log "✓ Manifest created: $manifest_file"
}

# ─── Send Notification ──────────────────────────────────────────────────────
send_notification() {
    local status="$1"
    local message="$2"
    
    if [ -n "$ALERT_EMAIL" ]; then
        local subject="QuantLib Backup $status - $HOSTNAME"
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" || true
    fi
    
    # Log to syslog
    logger -t quantlib-backup "$status: $message"
}

# ─── Main Execution ─────────────────────────────────────────────────────────
main() {
    log "========================================="
    log "QuantLib Pro Backup Started ($BACKUP_TYPE)"
    log "========================================="
    
    local start_time=$(date +%s)
    local backup_files=()
    
    # Run preflight checks
    preflight_checks
    
    # Perform backups
    backup_files+=( $(backup_data) )
    backup_files+=( $(backup_logs) )
    
    if [ "$DB_ENABLED" = "true" ]; then
        backup_files+=( $(backup_database) )
    fi
    
    if [ "$REDIS_ENABLED" = "true" ]; then
        backup_redis
    fi
    
    # Upload to cloud
    for file in "${backup_files[@]}"; do
        if [ -n "$file" ] && [ -f "$file" ]; then
            upload_to_cloud "$file"
        fi
    done
    
    # Generate manifest
    generate_manifest
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Calculate execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "========================================="
    log "Backup Completed Successfully (${duration}s)"
    log "========================================="
    
    send_notification "SUCCESS" "Backup completed in ${duration}s. See $BACKUP_LOG for details."
}

# ─── Error Handling ─────────────────────────────────────────────────────────
trap 'error "Backup failed at line $LINENO"; send_notification "FAILED" "Backup failed. Check $BACKUP_LOG for details."; exit 1' ERR

# Run main function
main "$@"
