# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# install git - TODO: remove after testing
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN echo "hi dad"

# Copy requirements first to leverage Docker cache
COPY pyproject.toml .
RUN pip install --no-cache-dir poetry
RUN pip install psutil flask

RUN #pip install agentstack
RUN pip install git+https://github.com/bboynton97/AgentStack.git@deploy
RUN mkdir src
RUN cp /usr/local/lib/python3.11/site-packages/agentstack/deploy/serve.py ./src

RUN pip uninstall -y agentstack

RUN apt-get update && apt-get install -y gcc
RUN POETRY_VIRTUALENVS_CREATE=false
RUN poetry config virtualenvs.create false && poetry install

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 6969

# Command to run the application
CMD ["python", "src/serve.py"]
#CMD ["sleep", "infinity"]