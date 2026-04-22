#!/usr/bin/env bash
set -euo pipefail

# Attente de la base (sauf si SQLite)
if [ "${USE_SQLITE3:-False}" != "True" ] && [ -n "${DB_HOST:-}" ]; then
    echo "[entrypoint] Attente de la base de données ${DB_HOST}:${DB_PORT:-3306}..."
    until nc -z "${DB_HOST}" "${DB_PORT:-3306}"; do
        sleep 1
    done
    echo "[entrypoint] Base de données disponible."
fi

# Migrations (activées par défaut)
if [ "${DJANGO_MIGRATE:-true}" = "true" ]; then
    echo "[entrypoint] Application des migrations..."
    python manage.py migrate --noinput
fi

# Collect static (désactivé par défaut, activé en prod via compose)
if [ "${DJANGO_COLLECTSTATIC:-false}" = "true" ]; then
    echo "[entrypoint] Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
fi

exec "$@"
