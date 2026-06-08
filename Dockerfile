# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copy project files
COPY . /app/

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Run via entrypoint (handles migrate + collectstatic + gunicorn)
ENTRYPOINT ["/app/entrypoint.sh"]
