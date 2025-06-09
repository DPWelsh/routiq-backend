FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
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

# Test script to identify failure point
RUN echo '#!/bin/bash' > /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Container startup beginning ==="' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Working directory: $(pwd) ==="' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Directory contents:"' >> /app/debug_startup.sh && \
    echo 'ls -la' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Python version: $(python --version) ==="' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Python path: $PYTHONPATH ==="' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Environment variables:"' >> /app/debug_startup.sh && \
    echo 'env | grep -E "(PORT|CLERK|SUPABASE|CREDENTIALS)" | sort' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing Python import ==="' >> /app/debug_startup.sh && \
    echo 'python -c "print(\"Python import test successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing FastAPI import ==="' >> /app/debug_startup.sh && \
    echo 'python -c "from fastapi import FastAPI; print(\"FastAPI import successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing uvicorn import ==="' >> /app/debug_startup.sh && \
    echo 'python -c "import uvicorn; print(\"Uvicorn import successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing src module import ==="' >> /app/debug_startup.sh && \
    echo 'python -c "import src; print(\"src module import successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing src.api import ==="' >> /app/debug_startup.sh && \
    echo 'python -c "import src.api; print(\"src.api import successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing src.api.main import ==="' >> /app/debug_startup.sh && \
    echo 'python -c "import src.api.main; print(\"src.api.main import successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: Testing app object access ==="' >> /app/debug_startup.sh && \
    echo 'python -c "from src.api.main import app; print(\"app object access successful\")"' >> /app/debug_startup.sh && \
    echo 'echo "=== DEBUG: All tests passed! Starting uvicorn... ==="' >> /app/debug_startup.sh && \
    echo 'exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}' >> /app/debug_startup.sh && \
    chmod +x /app/debug_startup.sh

# Use our debug script as the command
CMD ["/app/debug_startup.sh"] 