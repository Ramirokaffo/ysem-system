# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12

# =============================================================================
# Stage 1 — builder : construction des wheels des dépendances
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Toolchain nécessaire à la compilation des paquets qui n'ont pas de wheel
# manylinux disponible (cffi, cryptography, pillow, ...).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt ./

# Pré-compile toutes les dépendances (+ gunicorn utilisé en prod) en wheels.
# L'étage runtime ne fera plus qu'un `pip install --no-index` ultra rapide.
RUN pip wheel --wheel-dir /wheels -r requirements.txt gunicorn==23.0.0


# =============================================================================
# Stage 2 — runtime : image finale, sans toolchain
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=ysem.settings \
    PORT=8000 \
    PATH="/app/.local/bin:${PATH}"

# Librairies natives requises à l'exécution uniquement :
#   - libjpeg    : runtime Pillow (au cas où le wheel ne couvrirait pas tout)
#   - netcat     : attente de disponibilité de la DB dans l'entrypoint
#   - tini       : PID 1 correct (signaux, zombies)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        netcat-openbsd \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Utilisateur non-root
RUN groupadd --system --gid 1000 app \
    && useradd  --system --uid 1000 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app

# Installation depuis les wheels pré-construits (aucun compilateur ici)
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels

# Code applicatif
COPY --chown=app:app . /app

# Script d'entrypoint
COPY --chown=app:app docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Dossiers writables
RUN mkdir -p /app/static /app/media /app/logs \
    && chown -R app:app /app/static /app/media /app/logs

USER app

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]

# Commande par défaut = prod (Gunicorn). Overridée par docker-compose.dev.yml
CMD ["gunicorn", "ysem.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
