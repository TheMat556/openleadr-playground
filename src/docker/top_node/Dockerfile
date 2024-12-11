# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ../../../src /app/src
COPY ../../../Pipfile /app
COPY ../../../Pipfile.lock /app

# Install pipenv and any needed packages specified in Pipfile
RUN apt-get update && \
    apt-get install -y curl && \
    pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

# Run tst.py when the container launches
CMD ["pipenv", "run", "start-mock-node"]
