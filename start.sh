#!/usr/bin/env bash
# Render start command
set -o errexit

cd "$(dirname "$0")"

# Render sets $PORT
exec gunicorn quikgarage.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
