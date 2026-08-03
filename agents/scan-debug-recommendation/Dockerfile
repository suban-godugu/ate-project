FROM python:3.11-slim AS api

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY "scan debug data" "./scan debug data"
COPY model_weights.pth ./model_weights.pth
COPY .env.example ./.env.example

ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV API_HOST=0.0.0.0
ENV API_PORT=8005

EXPOSE 8005

CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8005}
