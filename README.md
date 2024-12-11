# Installation Guide

This guide will help you set up and run the server, client, and node using Scoop and Pipenv.

## Prerequisites

Ensure that [Scoop](https://scoop.sh/) is installed on Windows. For other operating systems, consider using a compatible package manager like Homebrew or Pacman. If Scoop is not installed, follow the installation instructions on its official website.

## Setup Instructions

1. **Add the `versions` bucket to Scoop:**

    ```bash
    scoop bucket add versions
    ```

2. **Install Python 3.12 using Scoop:**

    ```bash
    scoop install versions/python312
    ```

3. **Install Pipenv:**

    ```bash
    pip install pipenv
    ```

4. **Navigate to the project directory:**

    ```bash
    cd ./openleadr-playground
    ```

5. **Install project dependencies using Pipenv:**

    ```bash
    pipenv install
    ```

6. **Activate the Pipenv shell:**

    ```bash
    pipenv shell
    ```

7. **Start the house node:**

    ```bash
    pipenv run start-house-node
    ```

8. **Start the mock node:**

    ```bash
    pipenv run start-mock-node
    ```

## Containerized approach

This repository allows you to create hierarchical containers,
where each node has 2 children, this is only for testing purposes and
to demonstrate the capabilities of the implementation.
Note: The installation steps has to be followed before running the docker compose file.

1. **Create the docker compose file:**

    ```bash
    pipenv run create-docker-compose <layers>
    ```

2. **Start the containers:**

    ```bash
   docker compose up
    ```

3. **Stop the containers:**

    ```
    docker compose down
    ```
