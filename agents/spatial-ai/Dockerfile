# Default Dockerfile for ate-wafer-api on Render (no Torch / no model weights).
# Full CNN image remains available conceptually via requirements.txt + trained .pth later.
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" python-multipart

COPY render_demo_api.py .

ENV PYTHONUNBUFFERED=1
EXPOSE 10000

CMD ["sh", "-c", "uvicorn render_demo_api:app --host 0.0.0.0 --port ${PORT:-10000}"]
