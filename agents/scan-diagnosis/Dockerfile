# Multi-stage production Dockerfile — FastAPI diagnosis API
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY api/requirements.txt api-requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt \
    && pip install --no-cache-dir --user -r api-requirements.txt

COPY vendor/pyproject.toml /tmp/parser-engine/pyproject.toml
COPY vendor/parser_engine /tmp/parser-engine/parser_engine
RUN pip install --no-cache-dir --user /tmp/parser-engine

# ---------------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

ENTRYPOINT []
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
