#!/bin/sh
# Запуск на Timeweb: данные из deploy-data/, БД в /tmp, migrate на этой БД, 1 worker.
set -e
cd "$(dirname "$0")/.." 2>/dev/null || true

mkdir -p media /tmp

export DATABASE_PATH=/tmp/vinyl_collection.sqlite3

if [ -f deploy-data/db.sqlite3 ]; then
  cp -f deploy-data/db.sqlite3 "$DATABASE_PATH"
fi

# Схема auth/session на БД, с которой реально работает gunicorn
python3 manage.py migrate --noinput

if [ -d deploy-data/media ]; then
  cp -r deploy-data/media/. media/ 2>/dev/null || true
fi

exec gunicorn vinylsite.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
