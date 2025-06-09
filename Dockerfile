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

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port (use default 8000, Railway will override with PORT env var)
EXPOSE 8000

# Temporarily disable health check to debug startup issues
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application with verbose logging and error handling
CMD ["sh", "-c", "echo 'Starting application on port ${PORT:-8000}...' && echo 'Environment check:' && env | grep -E '(PORT|CREDENTIALS|SUPABASE|CLERK)' && python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info --access-log"] 