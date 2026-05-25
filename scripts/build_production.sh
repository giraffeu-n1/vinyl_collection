#!/bin/sh
# Сборка на Timeweb App Platform (вся логика здесь — в панели только: sh scripts/build_production.sh)
set -e

cd "$(dirname "$0")/.." 2>/dev/null || true

pip3 install --upgrade -r requirements-prod.txt

git rev-parse --short HEAD > BUILD_COMMIT.txt 2>/dev/null || true

mkdir -p media

if [ -f deploy-data/db.sqlite3 ]; then
  cp deploy-data/db.sqlite3 db.sqlite3
fi

if [ -d deploy-data/media ]; then
  cp -r deploy-data/media .
fi

python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
python3 manage.py create_vinyl_admin
