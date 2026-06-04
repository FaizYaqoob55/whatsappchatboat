FROM python:3.11-slim

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Create required directories
RUN mkdir -p data logs

# Python dependencies pehle copy karo (layer caching ke liye)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code copy karo
COPY . .

# Logs folder
RUN mkdir -p logs

# Non-root user (security)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Port expose karo
EXPOSE 8000

# Railway manages healthchecks externally via healthcheckPath setting
# No need for Docker HEALTHCHECK directive

# Production mein gunicorn use karo
# Shell form enables $PORT expansion; fallback to 8000 for local dev
CMD gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 0.0.0.0:${PORT:-8000} \
    --access-logfile - \
    --error-logfile -
