# ─────────────────────────────────────────────
# ntFAST Backend — FastAPI + Uvicorn
# Build context: project root (for ml_service access)
# ─────────────────────────────────────────────
FROM python:3.11-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Backend deps ────────────────────
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy backend code ───────────────────────
COPY backend/ .

# Create directories
RUN mkdir -p /app/uploads

# Expose port (Railway uses $PORT)
EXPOSE ${PORT:-8000}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run uvicorn — Railway sets PORT env var
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
