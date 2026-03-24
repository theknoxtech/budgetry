#!/bin/bash
set -e

DB_PATH="/app/instance/budgetry.db"

# If Litestream replica URL is configured, use Litestream to manage the DB
if [ -n "$LITESTREAM_REPLICA_URL" ]; then
    echo "Litestream replication enabled: $LITESTREAM_REPLICA_URL"

    # Restore the database from the replica if it exists and local DB doesn't
    if [ ! -f "$DB_PATH" ]; then
        echo "Restoring database from replica..."
        litestream restore -if-replica-exists -o "$DB_PATH" "$LITESTREAM_REPLICA_URL"
    fi

    # Start gunicorn under Litestream (replicates changes continuously)
    exec litestream replicate -exec "gunicorn -b 0.0.0.0:5000 'app:create_app()'" "$DB_PATH" "$LITESTREAM_REPLICA_URL"
else
    echo "Litestream not configured. Running without replication."
    exec gunicorn -b 0.0.0.0:5000 "app:create_app()"
fi
