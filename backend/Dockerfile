FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8888

EXPOSE 8888

# Hardcode 8888 to match Railway public networking; ignore broken $PORT expansion.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
