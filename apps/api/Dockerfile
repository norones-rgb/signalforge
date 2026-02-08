FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY apps/api/pyproject.toml /app/pyproject.toml
COPY apps/api/alembic.ini /app/alembic.ini
COPY apps/api/start.sh /app/start.sh
COPY apps/api/app /app/app

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir . \
    && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
