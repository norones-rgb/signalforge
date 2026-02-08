#!/usr/bin/env sh
set -e

if [ "${MIGRATE_ON_START:-false}" = "true" ]; then
  echo "Running migrations..."
  alembic -c /app/alembic.ini upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
