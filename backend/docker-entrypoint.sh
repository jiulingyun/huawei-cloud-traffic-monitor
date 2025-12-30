#!/bin/sh
set -e

# Ensure data and logs dirs exist
mkdir -p /app/data /app/logs

# If database missing, run initialization
DB_FILE="/app/data/app.db"
if [ ! -f "$DB_FILE" ]; then
  echo "Database not found, initializing..."
  python /app/init_db.py || {
    echo "Database init failed"; exit 1;
  }
else
  echo "Database exists, skipping init"
fi

# Exec the command (uvicorn) passed as CMD in Dockerfile
exec "$@"


