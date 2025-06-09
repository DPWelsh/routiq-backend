FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY sql/ ./sql/
COPY config/ ./config/

# Set Python path explicitly
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port (use default 8000, Railway will override with PORT env var)
EXPOSE 8000

# Re-enable health check with minimal endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Debug startup command with more explicit paths
CMD ["sh", "-c", "echo 'Container starting...' && echo 'Working directory:' && pwd && echo 'Python version:' && python --version && echo 'Python path:' && echo $PYTHONPATH && echo 'Directory contents:' && ls -la && echo 'src contents:' && ls -la src/ && echo 'Environment variables:' && env | grep -E '(PORT|CREDENTIALS|SUPABASE|CLERK|PYTHON)' && echo 'Starting uvicorn...' && cd /app && python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug"] 