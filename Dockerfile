# ===========================================
# Job Application Tracker - Production Dockerfile
# ===========================================

# Stage 1: Build stage
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements/base.txt requirements/production.txt /tmp/requirements/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements/production.txt


# Stage 2: Production stage
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Provide a build-time SECRET_KEY for collectstatic
ARG SECRET_KEY=build-time-secret-key
ENV SECRET_KEY=${SECRET_KEY}

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup . .

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/mediafiles && \
    chown -R appuser:appgroup /app/staticfiles /app/mediafiles

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Switch to non-root user
USER appuser

# Expose port (Railway uses PORT env variable)
EXPOSE 8000

# Health check (disabled for Railway as it uses PORT variable)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:${PORT:-8000}/api/v1/analytics/live/ || exit 1

# Run gunicorn (Railway will override with its own PORT)
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 2 --worker-class gthread --worker-tmp-dir /dev/shm --access-logfile - --error-logfile - config.wsgi:application
