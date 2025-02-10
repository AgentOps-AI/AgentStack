FROM python:3.12-slim-bookworm
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

WORKDIR /app

RUN apt update && apt install -y git gcc build-essential tree
RUN apt clean

# Install uv
RUN pip install --no-cache-dir uv

# Copy everything since we're installing local package
COPY . .

RUN uv pip install --system psutil
RUN uv pip install --system flask
RUN uv pip install --system gunicorn
RUN uv pip install --system git+https://github.com/AgentOps-AI/AgentStack.git@deploy-command
RUN mkdir -p src
RUN cp /usr/local/lib/python3.12/site-packages/agentstack/serve/serve.py ./src
RUN uv pip install --system .

# Create Gunicorn config
RUN echo 'import multiprocessing\n\
bind = "0.0.0.0:6969"\n\
workers = 1\n\
threads = 1\n\
worker_class = "sync"\n\
max_requests = 1\n\
max_requests_jitter = 0\n\
timeout = 300\n\
keepalive = 2\n\
worker_connections = 1\n\
errorlog = "-"\n\
accesslog = "-"\n\
capture_output = True\n\
def post_worker_init(worker):\n\
    worker.nr = 1' > gunicorn.conf.py

# Expose the port
EXPOSE 6969

# Use Gunicorn with config file
CMD ["gunicorn", "--config", "gunicorn.conf.py", "src.serve:app"]