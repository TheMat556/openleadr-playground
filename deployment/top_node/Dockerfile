FROM python:3.12-slim AS builder

# Set the home directory for the app user
ENV HOME=/home/appuser \
    # Adding these environment variables in builder stage only
    PIPENV_VENV_IN_PROJECT=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    # Disable pip cache and bytecode compilation to reduce image size
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create the app user and install dependencies in one layer
RUN apt-get update && \
    apt-get --no-install-recommends install -y curl && \
    addgroup --system appuser && \
    adduser --disabled-password --gecos '' --system --ingroup appuser appuser && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip pipenv

WORKDIR $HOME/app

# Copy only dependency files first to leverage Docker cache
COPY Pipfile Pipfile.lock $HOME/app/
RUN chown appuser:appuser $HOME/app Pipfile Pipfile.lock

# Install dependencies as appuser
USER appuser
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of the application
USER root
COPY src/ $HOME/app/src/
COPY env_variables.json $HOME/app/
RUN chown -R appuser:appuser $HOME/app/src $HOME/app/env_variables.json

# Second stage
FROM python:3.12-slim

ENV HOME=/home/appuser \
    # Disable pip cache and bytecode compilation
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create app user and install minimal requirements in one layer
RUN addgroup --system appuser && \
    adduser --disabled-password --gecos '' --system --ingroup appuser appuser && \
    apt-get update && \
    apt-get --no-install-recommends install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir pipenv

WORKDIR $HOME/app

# Create and set permissions for the data directory
RUN mkdir -p $HOME/app/data && \
    chown -R appuser:appuser $HOME/app

# Copy application from builder
COPY --from=builder --chown=appuser:appuser $HOME/app $HOME/app

USER appuser

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${REST_API_PORT}/health || exit 1

# Set the entry point to run the top node module
ENTRYPOINT ["pipenv", "run", "python", "-m", "src.adr_node.top_node"]
