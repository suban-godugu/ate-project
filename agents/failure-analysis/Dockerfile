FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Shared Parser Engine (imported by ingestion parsers at startup)
COPY vendor/pyproject.toml /tmp/parser-engine/pyproject.toml
COPY vendor/parser_engine /tmp/parser-engine/parser_engine
RUN pip install --no-cache-dir /tmp/parser-engine && rm -rf /tmp/parser-engine

COPY . /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV CELERY_ENABLED=false

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
