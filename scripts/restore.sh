#!/bin/bash

# ============================================================================
# QuantLib Pro - Restore Script
# ============================================================================
# Description: Restore data from backups
# Usage: ./restore.sh <backup_timestamp> [--data|--logs|--database|--all]
# Example: ./restore.sh 20240115_020000 --all
# ============================================================================

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DATA_DIR="${DATA_DIR:-./data}"
LOG_DIR="${LOG_DIR:-./logs}"
RESTORE_LOG="./restore_$(date +%Y%m%d_%H%M%S).log"

# Cloud storage
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
GCS_BUCKET="${GCS_BACKUP_BUCKET:-}"
AZURE_STORAGE_CONTAINER="${AZURE_STORAGE_CONTAINER:-}"

# Database
DB_TYPE="${DATABASE_TYPE:-postgresql}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-quantlib_pro}"
DB_USER="${DATABASE_USER:-quantlib}"

# ─── Logging ────────────────────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$RESTORE_LOG"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$RESTORE_LOG" >&2
}

# ─── Usage ──────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 <backup_timestamp> [--data|--logs|--database|--redis|--all]

Options:
  <backup_timestamp>  Timestamp of backup (e.g., 20240115_020000)
  --data              Restore data directory only
  --logs              Restore logs only
  --database          Restore database only
  --redis             Restore Redis only
  --all               Restore everything (default)
  --from-s3           Download from S3 first
  --from-gcs          Download from GCS first
  --from-azure        Download from Azure first
  --dry-run           Show what would be restored without doing it
  
Examples:
  $0 20240115_020000 --all
  $0 20240115_020000 --data --from-s3
  $0 20240115_020000 --database --dry-run

EOF
    exit 1
}

# ─── Parse Arguments ────────────────────────────────────────────────────────
if [ $# -lt 1 ]; then
    usage
fi

TIMESTAMP="$1"
shift

RESTORE_DATA=false
RESTORE_LOGS=false
RESTORE_DATABASE=false
RESTORE_REDIS=false
RESTORE_ALL=true
FROM_CLOUD=""
DRY_RUN=false

while [ $# -gt 0 ]; do
    case "$1" in
        --data)
            RESTORE_DATA=true
            RESTORE_ALL=false
            ;;
        --logs)
            RESTORE_LOGS=true
            RESTORE_ALL=false
            ;;
        --database)
            RESTORE_DATABASE=true
            RESTORE_ALL=false
            ;;
        --redis)
            RESTORE_REDIS=true
            RESTORE_ALL=false
            ;;
        --all)
            RESTORE_ALL=true
            ;;
        --from-s3)
            FROM_CLOUD="s3"
            ;;
        --from-gcs)
            FROM_CLOUD="gcs"
            ;;
        --from-azure)
            FROM_CLOUD="azure"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        *)
            error "Unknown option: $1"
            usage
            ;;
    esac
    shift
done

# If --all, enable everything
if [ "$RESTORE_ALL" = true ]; then
    RESTORE_DATA=true
    RESTORE_LOGS=true
    RESTORE_DATABASE=true
    RESTORE_REDIS=true
fi

# ─── Download from Cloud ────────────────────────────────────────────────────
download_from_cloud() {
    log "=== Downloading backups from cloud ==="
    
    mkdir -p "$BACKUP_DIR"
    
    case "$FROM_CLOUD" in
        s3)
            if [ -z "$S3_BUCKET" ]; then
                error "S3_BACKUP_BUCKET not set"
                exit 1
            fi
            log "Downloading from S3: s3://$S3_BUCKET/"
            aws s3 cp "s3://$S3_BUCKET/" "$BACKUP_DIR/" --recursive --exclude "*" --include "*${TIMESTAMP}*"
            ;;
        gcs)
            if [ -z "$GCS_BUCKET" ]; then
                error "GCS_BACKUP_BUCKET not set"
                exit 1
            fi
            log "Downloading from GCS: gs://$GCS_BUCKET/"
            gsutil -m cp "gs://$GCS_BUCKET/*${TIMESTAMP}*" "$BACKUP_DIR/"
            ;;
        azure)
            if [ -z "$AZURE_STORAGE_CONTAINER" ]; then
                error "AZURE_STORAGE_CONTAINER not set"
                exit 1
            fi
            log "Downloading from Azure"
            az storage blob download-batch \
                --account-name "${AZURE_STORAGE_ACCOUNT:-}" \
                --source "$AZURE_STORAGE_CONTAINER" \
                --destination "$BACKUP_DIR" \
                --pattern "*${TIMESTAMP}*"
            ;;
    esac
    
    log "✓ Download completed"
}

# ─── Verify Backups Exist ───────────────────────────────────────────────────
verify_backups() {
    log "=== Verifying backup files exist ==="
    
    local missing_files=()
    
    if [ "$RESTORE_DATA" = true ]; then
        local data_backup=$(find "$BACKUP_DIR" -name "data_${TIMESTAMP}.*" | head -1)
        if [ -z "$data_backup" ]; then
            missing_files+=("data_${TIMESTAMP}")
        fi
    fi
    
    if [ "$RESTORE_LOGS" = true ]; then
        local logs_backup=$(find "$BACKUP_DIR" -name "logs_${TIMESTAMP}.*" | head -1)
        if [ -z "$logs_backup" ]; then
            log "! No logs backup found (non-critical)"
        fi
    fi
    
    if [ "$RESTORE_DATABASE" = true ]; then
        local db_backup=$(find "$BACKUP_DIR" -name "database_${TIMESTAMP}.*" | head -1)
        if [ -z "$db_backup" ]; then
            missing_files+=("database_${TIMESTAMP}")
        fi
    fi
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Missing backup files: ${missing_files[*]}"
        error "Available backups in $BACKUP_DIR:"
        ls -lh "$BACKUP_DIR"
        exit 1
    fi
    
    log "✓ All required backup files found"
}

# ─── Create Backup Before Restore ───────────────────────────────────────────
create_pre_restore_backup() {
    log "=== Creating pre-restore backup ==="
    
    local pre_restore_dir="$BACKUP_DIR/pre_restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$pre_restore_dir"
    
    if [ -d "$DATA_DIR" ]; then
        log "Backing up current data directory..."
        tar -czf "$pre_restore_dir/data.tar.gz" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"
    fi
    
    log "✓ Pre-restore backup saved to: $pre_restore_dir"
}

# ─── Restore Data ───────────────────────────────────────────────────────────
restore_data() {
    log "=== Restoring Data Directory ==="
    
    local data_backup=$(find "$BACKUP_DIR" -name "data_${TIMESTAMP}.*" | head -1)
    
    if [ -z "$data_backup" ]; then
        error "Data backup not found for timestamp $TIMESTAMP"
        return 1
    fi
    
    log "Found backup: $data_backup"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would restore data from: $data_backup"
        log "[DRY RUN] Target directory: $DATA_DIR"
        return 0
    fi
    
    # Stop application if running
    log "Stopping application (if running)..."
    if command -v docker &> /dev/null; then
        docker stop quantlib-app 2>/dev/null || true
    fi
    
    # Remove existing data (with safety check)
    if [ -d "$DATA_DIR" ]; then
        log "Moving existing data to $DATA_DIR.backup..."
        mv "$DATA_DIR" "${DATA_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Extract backup
    log "Extracting data backup..."
    mkdir -p "$(dirname "$DATA_DIR")"
    
    if [[ "$data_backup" == *.gz ]]; then
        tar -xzf "$data_backup" -C "$(dirname "$DATA_DIR")"
    else
        tar -xf "$data_backup" -C "$(dirname "$DATA_DIR")"
    fi
    
    log "✓ Data restored successfully"
}

# ─── Restore Logs ───────────────────────────────────────────────────────────
restore_logs() {
    log "=== Restoring Logs ==="
    
    local logs_backup=$(find "$BACKUP_DIR" -name "logs_${TIMESTAMP}.*" | head -1)
    
    if [ -z "$logs_backup" ]; then
        log "! No logs backup found (skipping)"
        return 0
    fi
    
    log "Found backup: $logs_backup"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would restore logs from: $logs_backup"
        return 0
    fi
    
    # Backup existing logs
    if [ -d "$LOG_DIR" ]; then
        mv "$LOG_DIR" "${LOG_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Extract backup
    mkdir -p "$(dirname "$LOG_DIR")"
    
    if [[ "$logs_backup" == *.gz ]]; then
        tar -xzf "$logs_backup" -C "$(dirname "$LOG_DIR")"
    else
        tar -xf "$logs_backup" -C "$(dirname "$LOG_DIR")"
    fi
    
    log "✓ Logs restored successfully"
}

# ─── Restore Database ───────────────────────────────────────────────────────
restore_database() {
    log "=== Restoring Database ==="
    
    local db_backup=$(find "$BACKUP_DIR" -name "database_${TIMESTAMP}.*" | head -1)
    
    if [ -z "$db_backup" ]; then
        error "Database backup not found for timestamp $TIMESTAMP"
        return 1
    fi
    
    log "Found backup: $db_backup"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would restore database from: $db_backup"
        return 0
    fi
    
    # Decompress if needed
    local restore_file="$db_backup"
    if [[ "$db_backup" == *.gz ]]; then
        log "Decompressing database backup..."
        gunzip -c "$db_backup" > "${db_backup%.gz}"
        restore_file="${db_backup%.gz}"
    fi
    
    # Restore based on database type
    case "$DB_TYPE" in
        postgresql)
            log "Restoring PostgreSQL database..."
            # Drop existing database (with confirmation)
            log "WARNING: This will drop the existing database!"
            read -p "Continue? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
                log "Restore cancelled by user"
                exit 0
            fi
            
            PGPASSWORD="${DATABASE_PASSWORD:-}" dropdb \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                "$DB_NAME" || true
            
            PGPASSWORD="${DATABASE_PASSWORD:-}" createdb \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                "$DB_NAME"
            
            PGPASSWORD="${DATABASE_PASSWORD:-}" pg_restore \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                "$restore_file"
            ;;
        mysql)
            log "Restoring MySQL database..."
            mysql \
                -h "$DB_HOST" \
                -P "$DB_PORT" \
                -u "$DB_USER" \
                -p"${DATABASE_PASSWORD:-}" \
                "$DB_NAME" \
                < "$restore_file"
            ;;
        sqlite)
            log "Restoring SQLite database..."
            local db_file="${DATABASE_FILE:-data/quantlib.db}"
            cp "$restore_file" "$db_file"
            ;;
    esac
    
    log "✓ Database restored successfully"
}

# ─── Restore Redis ──────────────────────────────────────────────────────────
restore_redis() {
    log "=== Restoring Redis ==="
    
    local redis_backup=$(find "$BACKUP_DIR" -name "redis_${TIMESTAMP}.*" | head -1)
    
    if [ -z "$redis_backup" ]; then
        log "! No Redis backup found (skipping)"
        return 0
    fi
    
    log "Found backup: $redis_backup"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would restore Redis from: $redis_backup"
        return 0
    fi
    
    # Stop Redis
    log "Stopping Redis..."
    if command -v systemctl &> /dev/null; then
        systemctl stop redis || true
    elif command -v service &> /dev/null; then
        service redis stop || true
    fi
    
    # Decompress if needed
    local restore_file="$redis_backup"
    if [[ "$redis_backup" == *.gz ]]; then
        gunzip -c "$redis_backup" > "${redis_backup%.gz}"
        restore_file="${redis_backup%.gz}"
    fi
    
    # Copy dump.rdb
    local redis_dump="/var/lib/redis/dump.rdb"
    cp "$restore_file" "$redis_dump"
    chown redis:redis "$redis_dump" 2>/dev/null || true
    
    # Start Redis
    log "Starting Redis..."
    if command -v systemctl &> /dev/null; then
        systemctl start redis
    elif command -v service &> /dev/null; then
        service redis start
    fi
    
    log "✓ Redis restored successfully"
}

# ─── Verify Restore ─────────────────────────────────────────────────────────
verify_restore() {
    log "=== Verifying Restore ==="
    
    if [ "$RESTORE_DATA" = true ]; then
        if [ -d "$DATA_DIR" ]; then
            log "✓ Data directory exists"
        else
            error "Data directory not found after restore!"
            exit 1
        fi
    fi
    
    if [ "$RESTORE_DATABASE" = true ]; then
        case "$DB_TYPE" in
            postgresql)
                if PGPASSWORD="${DATABASE_PASSWORD:-}" psql \
                    -h "$DB_HOST" \
                    -p "$DB_PORT" \
                    -U "$DB_USER" \
                    -d "$DB_NAME" \
                    -c "SELECT 1;" &>/dev/null; then
                    log "✓ Database connection successful"
                else
                    error "Database connection failed!"
                    exit 1
                fi
                ;;
        esac
    fi
    
    log "✓ Restore verification completed"
}

# ─── Main Execution ─────────────────────────────────────────────────────────
main() {
    log "========================================="
    log "QuantLib Pro Restore Started"
    log "Timestamp: $TIMESTAMP"
    log "========================================="
    
    # Download from cloud if needed
    if [ -n "$FROM_CLOUD" ]; then
        download_from_cloud
    fi
    
    # Verify backups exist
    verify_backups
    
    # Create pre-restore backup
    if [ "$DRY_RUN" = false ]; then
        create_pre_restore_backup
    fi
    
    # Perform restore
    if [ "$RESTORE_DATA" = true ]; then
        restore_data
    fi
    
    if [ "$RESTORE_LOGS" = true ]; then
        restore_logs
    fi
    
    if [ "$RESTORE_DATABASE" = true ]; then
        restore_database
    fi
    
    if [ "$RESTORE_REDIS" = true ]; then
        restore_redis
    fi
    
    # Verify restore
    if [ "$DRY_RUN" = false ]; then
        verify_restore
    fi
    
    log "========================================="
    log "Restore Completed Successfully"
    log "Log file: $RESTORE_LOG"
    log "========================================="
    
    if [ "$DRY_RUN" = false ]; then
        log ""
        log "Next steps:"
        log "1. Start the application"
        log "2. Verify functionality"
        log "3. Check logs for errors"
        log ""
        log "To start application:"
        log "  docker-compose up -d"
    fi
}

# ─── Error Handling ─────────────────────────────────────────────────────────
trap 'error "Restore failed at line $LINENO"; exit 1' ERR

# Run main function
main
