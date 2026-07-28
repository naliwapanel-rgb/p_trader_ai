#!/bin/sh
set -eu

umask 027

if [ "${RUN_DATABASE_MIGRATIONS:-true}" = "true" ]; then
    echo "Applying database migrations..."
    python -m alembic upgrade head
fi

echo "Starting P-TRADER AI backend..."
exec "$@"
