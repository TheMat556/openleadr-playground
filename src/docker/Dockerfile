# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install pipenv and any needed packages specified in Pipfile
RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

# Make port 80 available to the world outside this container
EXPOSE 80

# Run tst.py when the container launches
CMD ["pipenv", "run", "python", "tst.py", "tst"]