FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get --no-install-recommends install -y curl && \
    addgroup --system appuser && \
    adduser --disabled-password --gecos '' --system --ingroup appuser appuser && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ../../../src /app/src
COPY ../../../Pipfile /app
COPY ../../../env_variables.json /app
COPY ../../../Pipfile.lock /app

RUN chown -R appuser:appuser /app

ENV PIPENV_VENV_IN_PROJECT=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    HOME=/home/appuser

RUN pip install --upgrade pip && \
    pip install pipenv

USER appuser

RUN pipenv install --deploy --ignore-pipfile

CMD ["pipenv", "run", "start-mock-node"]
