FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY workers/pyproject.toml /app/pyproject.toml
COPY workers/celery_app.py /app/celery_app.py
COPY workers/tasks /app/tasks
COPY apps/api/app /app/app
COPY shared /app/shared

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir .

