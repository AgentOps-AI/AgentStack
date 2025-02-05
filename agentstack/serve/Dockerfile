FROM python:3.12-slim-bookworm
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /app

RUN apt update && apt install -y git gcc build-essential tree
RUN apt clean

# Copy requirements first to leverage Docker cache
COPY pyproject.toml .
RUN pip install --no-cache-dir uv
RUN pip install psutil flask

RUN #pip install agentstack
RUN pip install git+https://github.com/AgentOps-AI/AgentStack.git@deploy-command
RUN mkdir src
RUN cp /usr/local/lib/python3.12/site-packages/agentstack/serve/serve.py ./src

RUN pip uninstall -y agentstack

RUN uv venv
RUN source .venv/bin/activate
RUN uv pip install --requirements pyproject.toml

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 6969

# Command to run the application
CMD ["/app/.venv/bin/agentstack", "run"]