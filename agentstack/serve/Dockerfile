FROM python:3.12-slim-bookworm
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /app

RUN apt update && apt install -y git gcc build-essential tree
RUN apt clean

# Install uv
RUN pip install --no-cache-dir uv

# Copy everything since we're installing local package
COPY . .
# install local version of agentstack for local dev
#COPY ../../ agentstack
RUN #ls -a agentstack


# Debug: Try installing packages one at a time
RUN uv pip install --system psutil
RUN uv pip install --system flask
RUN uv pip install --system git+https://github.com/AgentOps-AI/AgentStack.git@deploy-command #install on cloud #cache 4
RUN #cd agentstack && uv pip install --system .
RUN mkdir -p src
RUN cp /usr/local/lib/python3.12/site-packages/agentstack/serve/serve.py ./src
RUN #cp agentstack/serve/serve.py ./src
RUN #uv pip uninstall -y agentstack
RUN uv pip install --system .

# Expose the port
EXPOSE 6969

# Use python directly since we're installing to system
CMD ["python", "src/serve.py"]