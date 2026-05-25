#!/bin/sh
# Запуск на Timeweb App Platform (без SFTP): данные из deploy-data/, одна worker для SQLite.
set -e
cd "$(dirname "$0")/.." 2>/dev/null || true

mkdir -p media
mkdir -p /tmp

if [ -f deploy-data/db.sqlite3 ]; then
  cp -f deploy-data/db.sqlite3 /tmp/vinyl_collection.sqlite3
  export DATABASE_PATH=/tmp/vinyl_collection.sqlite3
fi

if [ -d deploy-data/media ]; then
  cp -r deploy-data/media/. media/ 2>/dev/null || true
fi

exec gunicorn vinylsite.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
