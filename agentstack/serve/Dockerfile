FROM python:3.12-slim-bookworm
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /app

RUN apt update && apt install -y git gcc build-essential tree
RUN apt clean && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy everything since we're installing local package
COPY . .

RUN uv pip install --system psutil
RUN uv pip install --system flask
RUN uv pip install --system gunicorn
RUN uv pip install --system git+https://github.com/AgentOps-AI/AgentStack.git@deploy-command # 1
RUN mkdir -p src
RUN cp /usr/local/lib/python3.12/site-packages/agentstack/serve/serve.py ./src
RUN cp /usr/local/lib/python3.12/site-packages/agentstack/serve/gunicorn.config.py ./src
RUN uv pip install --system .
RUN rm -rf /root/.cache/uv/* /root/.cache/pip/* /tmp/*

# Expose the port
EXPOSE 6969

# Use Gunicorn with config file
CMD ["gunicorn", "--config", "src/gunicorn.config.py", "src.serve:app"]