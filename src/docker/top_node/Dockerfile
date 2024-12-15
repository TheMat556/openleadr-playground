# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ../../../src /app/src
COPY ../../../Pipfile /app
COPY ../../../Pipfile.lock /app

# Change ownership of the /app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Install pipenv and any needed packages specified in Pipfile
RUN apt-get update && \
    apt-get install -y curl && \
    pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --deploy --ignore-pipfile && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Run tst.py when the container launches
CMD ["pipenv", "run", "start-mock-node"]
