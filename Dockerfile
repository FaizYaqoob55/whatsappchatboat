FROM python:3.11-slim

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production mein gunicorn use karo
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
