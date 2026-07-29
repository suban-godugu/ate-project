# syntax=docker/dockerfile:1

FROM python:3.11-slim AS backend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY models ./models
COPY scripts ./scripts
COPY pyproject.toml .
COPY .env.example .env.example

ENV WAFERVISION_ENV=production
ENV WAFERVISION_API_HOST=0.0.0.0
ENV WAFERVISION_API_PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "src.api"]
