FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies for production)
RUN uv sync --no-dev --frozen

# Copy only necessary application files
COPY app/ ./app/
COPY src/ ./src/
COPY main.py ./
COPY config.py ./

# Copy essential data files only
COPY data/*.xlsx ./data/ 2>/dev/null || true
COPY cache/ ./cache/ 2>/dev/null || true
COPY *.xlsx ./ 2>/dev/null || true

# Create cache directory if it doesn't exist
RUN mkdir -p cache/hs_code_cache

# Set environment variables
ENV PYTHONPATH=/app
ENV UV_SYSTEM_PYTHON=1
ENV ENVIRONMENT=production

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8003}/health || exit 1

# Command to run the application  
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8003}"]