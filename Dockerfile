# syntax=docker/dockerfile:1
FROM debian:12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DJANGO_ENV_FILE=/app/.env \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 \
       python3-pip \
       python3-venv \
       python3-dev \
       build-essential \
       libpq-dev \
       curl \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && ln -sf /usr/bin/pip3 /usr/local/bin/pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --break-system-packages -r requirements.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

CMD ["./docker/entrypoint.sh"]