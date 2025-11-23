# Multi-stage Dockerfile for Research Assistant Tool

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-neo4j.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r requirements-neo4j.txt


# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p logs data backups && \
    chown -R appuser:appuser logs data backups

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Set environment variables
ENV FLASK_APP=web_ui/app.py
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
