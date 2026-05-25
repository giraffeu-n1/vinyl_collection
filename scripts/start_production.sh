#!/bin/sh
# Запуск на Timeweb: БД и media в /tmp (запись), данные из deploy-data/
set -e
cd "$(dirname "$0")/.." 2>/dev/null || true

export DATABASE_PATH=/tmp/vinyl_collection.sqlite3
export MEDIA_ROOT_PATH=/tmp/vinyl_media

mkdir -p /tmp "$MEDIA_ROOT_PATH"

if [ -f deploy-data/db.sqlite3 ]; then
  cp -f deploy-data/db.sqlite3 "$DATABASE_PATH"
fi

if [ -d deploy-data/media ]; then
  cp -r deploy-data/media/. "$MEDIA_ROOT_PATH"/
elif [ -d media ]; then
  cp -r media/. "$MEDIA_ROOT_PATH"/
fi

chmod -R u+rwX "$MEDIA_ROOT_PATH" 2>/dev/null || true

python3 manage.py migrate --noinput

exec gunicorn vinylsite.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
