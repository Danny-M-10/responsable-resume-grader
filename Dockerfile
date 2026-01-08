# Multi-stage build for FastAPI backend + React frontend

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/ .

# Build React app
RUN npm run build

# Stage 2: Python backend with frontend
FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 and asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python code (backend + existing modules)
COPY *.py ./
COPY backend/ ./backend/
COPY models.py ./
COPY config.py ./
COPY db.py ./
COPY auth.py ./
COPY utils.py ./
COPY storage.py ./
COPY ai_*.py ./
COPY resume_parser*.py ./
COPY candidate_ranker.py ./
COPY pdf_generator.py ./
COPY scoring_*.py ./
COPY industry_templates.py ./
COPY skills_researcher.py ./
COPY resume_database.py ./
COPY loading_components.py ./
COPY ui/ ./ui/
COPY assets/ ./assets/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Create directory for static files
RUN mkdir -p /app/static

# Update FastAPI to serve static files
# We'll handle this in main.py

ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
