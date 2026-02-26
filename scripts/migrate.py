#!/usr/bin/env python3
"""Database migration management script.

Usage:
    python scripts/migrate.py upgrade          # Run all migrations
    python scripts/migrate.py downgrade -1     # Rollback 1 migration
    python scripts/migrate.py current          # Show current revision
    python scripts/migrate.py history          # Show migration history
    python scripts/migrate.py timescale        # Run TimescaleDB migrations
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(command: list[str], env: dict = None) -> int:
    """Run a command and return the exit code."""
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    
    result = subprocess.run(command, env=env_vars)
    return result.returncode


def main():
    """Main migration script."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    
    # Set default database URL from .env
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    
    if action == "timescale":
        # Run migrations against TimescaleDB
        print("🔄 Running TimescaleDB migrations...")
        timescale_url = os.getenv(
            "TIMESCALE_URL",
            "postgresql://quantlib:changeme@localhost:5433/timeseries_db"
        )
        return run_command(
            ["alembic", "upgrade", "head"],
            env={"DATABASE_URL": timescale_url}
        )
    
    elif action == "upgrade":
        # Run migrations against PostgreSQL
        print("🔄 Running PostgreSQL migrations...")
        return run_command(["alembic", "upgrade", "head"])
    
    elif action == "downgrade":
        # Rollback migrations
        target = sys.argv[2] if len(sys.argv) > 2 else "-1"
        print(f"🔄 Rolling back to {target}...")
        return run_command(["alembic", "downgrade", target])
    
    elif action == "current":
        # Show current revision
        return run_command(["alembic", "current"])
    
    elif action == "history":
        # Show migration history
        return run_command(["alembic", "history"])
    
    elif action == "stamp":
        # Stamp database with current version (without running migrations)
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        print(f"📌 Stamping database at {revision}...")
        return run_command(["alembic", "stamp", revision])
    
    else:
        print(f"❌ Unknown action: {action}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
