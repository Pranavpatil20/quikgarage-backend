#!/usr/bin/env bash
# Render build command (run from repo root or backend/)
set -o errexit

cd "$(dirname "$0")"

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
