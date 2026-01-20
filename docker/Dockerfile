# Stage 1: Builder - Build dependencies
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt

# Build wheels for faster installation
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels \
    -r requirements.txt \
    -r requirements-dev.txt

# Stage 2: Runtime - Create final image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libmagic1 \
    curl \
    tzdata \
  && rm -rf /var/lib/apt/lists/*

# Timezone via TZ env
ARG TZ=UTC
ENV TZ=${TZ}
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Copy and install wheels from builder stage
COPY --from=builder /build/wheels /wheels
RUN pip install --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Create non-root user
RUN useradd -ms /bin/bash appuser

# Copy source code
COPY meatbot /app/meatbot
COPY static /app/static
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${WEB_APP_PORT:-8000}/health/live || exit 1

# Placeholder command (will be replaced by bot entrypoint later)
CMD ["/bin/sh", "-lc", "echo 'MeatBot app container ready'; sleep 365d"]


