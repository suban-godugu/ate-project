FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV BACKEND_HOST=0.0.0.0
EXPOSE 8041
CMD uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8041}
