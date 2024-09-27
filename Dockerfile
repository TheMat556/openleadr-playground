FROM ubuntu:latest
LABEL authors="matth"

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    pipx \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$PATH:/root/.local/bin"

RUN pipx install pipenv
WORKDIR /app

RUN git clone --depth 1 https://github.com/TheMat556/openleadr-playground .

#only for local docker deployment
#COPY Pipfile Pipfile.lock ./
#COPY src ./src

RUN pipenv install

RUN pipenv run start-node

ENTRYPOINT ["top", "-b"]
