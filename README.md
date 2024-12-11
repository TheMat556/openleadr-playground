# Basic Idea

This repository provides an implementation of a hierarchical network infrastructure utilizing the OpenADR protocol.
It offers a systematic approach to fair load distribution and integrates Loxone into the overall application.
The hierarchical structure ensures efficient communication and control across different nodes, facilitating robust and scalable energy management solutions.

## Installation Guide

This guide will help you set up and run the server, client, and node using Scoop and Pipenv.

## Prerequisites

Suggestion: Make sure somekind of package manager is installed on your system. For example, Scoop for Windows, Homebrew for macOS, or Pacman for Linux. This makes it easier to install and maintain different python version
This guide will specifically cover the installation of Python 3.12 using [Scoop](https://scoop.sh/) on Windows.

## Setup Instructions

### Basic Setup (Windows)

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

### Project Installation

1. **Navigate to the project directory:**

    ```bash
    cd ./openleadr-playground
    ```

2. **Install project dependencies using Pipenv:**

    ```bash
    pipenv install
    ```

3. **Activate the Pipenv shell:**

    ```bash
    pipenv shell
    ```

### Start nodes

The basic implementation of the OpenADR node provides a simple base node that can be easily extended.
The house, middle, and mock nodes are examples of such extensions.
Which will be used to demonstrate the hierarchical network infrastructure.

1**Start the house node:**

    ```bash
    pipenv run start-house-node
    ```

2**Start the mock node:**

    ```bash
    pipenv run start-mock-node
    ```

## Containerized approach

This repository allows you to create hierarchical containers,
where each node has 2 children (done for simplicity), this is only for testing purposes and
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
