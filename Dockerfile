# Single-service Cadence image for Railway: builds the Vite SPA, then serves it + the FastAPI
# API from one container (FastAPI mounts the built SPA at / and the API under /api). Build
# context = this directory (the project root).

# ---- 1) build the frontend ----
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2) backend + serve ----
FROM python:3.12-slim AS app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    FRONTEND_DIST=/app/frontend_dist
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Install the backend (editable: data files — migrations *.sql, taxonomy *.json — are read from src).
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src ./src
RUN pip install --upgrade pip && pip install -e .

COPY scripts/start.sh ./start.sh
COPY --from=frontend /fe/dist ./frontend_dist

EXPOSE 8000
# Shell form so ${PORT} expands; the script waits for the DB, seeds-if-empty, then execs uvicorn.
CMD ["sh", "/app/start.sh"]
