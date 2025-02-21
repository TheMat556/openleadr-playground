# Builder stage
FROM python:3.12-slim AS builder

# Set environment variables for builder stage
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    HOME="/home/appuser" \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies and create app user
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl \
        build-essential \
        gcc \
        g++ \
        pkg-config \
        python3-dev \
        libxml2-dev \
        libxslt1-dev \
        && \
    addgroup --system appuser && \
    adduser --disabled-password --gecos '' --system --ingroup appuser appuser && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create necessary directories
    mkdir -p /home/appuser/app && \
    mkdir -p /tmp/poetry_cache && \
    # Install poetry
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry && \
    # Set permissions
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /tmp/poetry_cache

WORKDIR /home/appuser/app

# Copy only dependency files first to leverage Docker cache
COPY --chown=appuser:appuser pyproject.toml poetry.lock ./

# Create a minimal README.md if it doesn't exist
RUN echo "# OpenLEADR Node\nA simple flexible multi-layer architecture for openleadr (openadr)." > README.md && \
    chown appuser:appuser README.md

# Install dependencies as appuser
USER appuser
RUN poetry install --only main --no-root

# Copy the rest of the application
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser env_variables.json ./

# Install the project itself
RUN poetry install --only main

# Production stage
FROM python:3.12-slim

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    HOME="/home/appuser" \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install minimal runtime dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        curl \
        libxml2 \
        libxslt1.1 \
        && \
    addgroup --system appuser && \
    adduser --disabled-password --gecos '' --system --ingroup appuser appuser && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Create necessary directories
    mkdir -p /home/appuser/app && \
    mkdir -p /home/appuser/app/data && \
    mkdir -p /tmp/poetry_cache && \
    # Install poetry
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry && \
    # Set permissions
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /tmp/poetry_cache

WORKDIR /home/appuser/app

# Copy application from builder
COPY --from=builder --chown=appuser:appuser /home/appuser/app /home/appuser/app

# Create startup script with proper escaping
RUN echo '#!/bin/sh\nif [ "$NODE_TYPE" = "network_dashboard" ]; then\n    exec poetry run start-network-dashboard\nelif [ "$NODE_TYPE" = "top_node" ]; then\n    exec poetry run start-top-node\nelif [ "$NODE_TYPE" = "intermediate_node" ]; then\n    exec poetry run start-intermediate-node\nelif [ "$NODE_TYPE" = "bottom_node" ]; then\n    exec poetry run start-bottom-node\nelse\n    echo "Unknown node type: $NODE_TYPE"\n    exit 1\nfi' > /home/appuser/app/start.sh && \
    chmod +x /home/appuser/app/start.sh && \
    chown appuser:appuser /home/appuser/app/start.sh

USER appuser

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${REST_API_PORT}/health || exit 1

# Make the node type configurable using build args
ARG NODE_TYPE=top_node
ARG OPENADR_LAYER_ID=0
ENV NODE_TYPE=${NODE_TYPE} \
    OPENADR_LAYER_ID=${OPENADR_LAYER_ID}

# Use the startup script as entrypoint
ENTRYPOINT ["/home/appuser/app/start.sh"]
