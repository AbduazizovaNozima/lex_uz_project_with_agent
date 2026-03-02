# ─────────────────────────────────────────────────────────────
# Dockerfile — LexAI Professional
# Build: docker build -f docker/Dockerfile -t lexai .
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System deps (psycopg2-binary still needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application sources
COPY . .

# Create output directories
RUN mkdir -p logs sessions lex_structured

# Expose FastAPI port
EXPOSE 8000

# Default command: run the unified entrypoint
CMD ["python", "main.py"]
