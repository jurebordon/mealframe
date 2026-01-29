#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting MealFrame API..."
exec gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8003 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
