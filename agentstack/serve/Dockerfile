FROM python:3.12-slim-bookworm
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /app

RUN apt update && apt install -y git gcc build-essential tree
RUN apt clean

COPY . .

# Install uv and create venv in one layer
RUN pip install --no-cache-dir uv \
    && uv venv \
    && . .venv/bin/activate \
    && uv pip install psutil flask \
    && uv pip install git+https://github.com/AgentOps-AI/AgentStack.git@deploy-command \
    && mkdir -p src \
    && cp /usr/local/lib/python3.12/site-packages/agentstack/serve/serve.py ./src \
    && uv pip uninstall -y agentstack \
    && uv pip install .

# Add venv to path
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port
EXPOSE 6969

# Use absolute path to be safe
CMD ["/app/.venv/bin/python", "src/serve.py"]