FROM python:3.12-slim-bookworm
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /app

RUN apt update && apt install -y git gcc build-essential tree
RUN apt clean

# Install uv
RUN pip install --no-cache-dir uv

# Copy everything since we're installing local package
COPY . .

# Debug: Try installing packages one at a time
RUN uv pip install --system psutil
RUN uv pip install --system flask
RUN uv pip install --system git+https://github.com/AgentOps-AI/AgentStack.git@deploy-command
RUN mkdir -p src
RUN cp /usr/local/lib/python3.12/site-packages/agentstack/serve/serve.py ./src
RUN #uv pip uninstall -y agentstack
RUN uv pip install --system .

# Expose the port
EXPOSE 6969

# Use python directly since we're installing to system
CMD ["python", "src/serve.py"]