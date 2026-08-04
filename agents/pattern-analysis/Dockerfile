FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared Parser Engine (required at import time by stil_parser / ate_parser)
COPY vendor/pyproject.toml /tmp/parser-engine/pyproject.toml
COPY vendor/parser_engine /tmp/parser-engine/parser_engine
RUN pip install --no-cache-dir /tmp/parser-engine && rm -rf /tmp/parser-engine

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8011

# Render injects $PORT — must expand via shell.
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8011}"]
