import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT') or '6969'}"
workers = 1
threads = 1
worker_class = "sync"
max_requests = 1
max_requests_jitter = 0
timeout = 300
keepalive = 2
worker_connections = 1
errorlog = "-"
accesslog = "-"
capture_output = True

def post_worker_init(worker):
    worker.nr = 1