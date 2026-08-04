FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared Parser Engine (same vendored package agents use)
COPY vendor/pyproject.toml vendor/README.md /tmp/parser-engine/
COPY vendor/parser_engine /tmp/parser-engine/parser_engine
RUN pip install --no-cache-dir /tmp/parser-engine && rm -rf /tmp/parser-engine

COPY . .

RUN chmod +x /app/start.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8888

# start.sh runs ARQ worker + uvicorn (PORT expanded at runtime).
CMD ["/app/start.sh"]
