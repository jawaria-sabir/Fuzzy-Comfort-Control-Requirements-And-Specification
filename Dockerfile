# ──────────────────────────────────────────────────────────
# Fuzzy Comfort Control System · Production Docker Image
# Base: Python 3.12-slim | WSGI: Gunicorn | Port: 5000
# ──────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="jawaria-sabir"
LABEL description="Fuzzy Comfort Control System — Mamdani Inference Engine"
LABEL version="2.0.0"

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd -m -u 1001 fuzzyapp
WORKDIR /app

# Install Python deps first (layer cache optimisation)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY --chown=fuzzyapp:fuzzyapp . .

USER fuzzyapp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

EXPOSE 5000

# Gunicorn: 4 workers, timeout 120s, access logs to stdout
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
