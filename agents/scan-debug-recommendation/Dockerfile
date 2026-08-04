# Default Dockerfile for Render Docker deploys (demo API stub).
# Full ML stack requires restoring src/data + src/models into the repo.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

COPY src ./src

ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV AUTO_TRAIN_ON_STARTUP=false
ENV STARTUP_WARM_CACHES=false
ENV REQUIRE_API_KEY=false

EXPOSE 8042

CMD uvicorn src.api.render_app:app --host 0.0.0.0 --port ${PORT:-8042}
