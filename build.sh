#!/usr/bin/env bash
# Build script Render — collectstatic + migrate
set -o errexit

echo "==> Installation des dépendances"
pip install -r requirements.txt

cd backend

echo "==> Collecte des fichiers statiques"
python manage.py collectstatic --no-input

echo "==> Migrations de la base de données"
python manage.py migrate --no-input

echo "==> Build terminé"
