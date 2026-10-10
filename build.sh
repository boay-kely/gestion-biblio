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

# Compte admin initial (optionnel via ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL)
if [ -n "${ADMIN_PASSWORD:-}" ]; then
  echo "==> Création du compte admin (si absent)"
  python manage.py ensure_admin
fi

echo "==> Build terminé"
