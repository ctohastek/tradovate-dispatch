import os
import multiprocessing

# Server socket
bind = os.getenv("BIND", "127.0.0.1:8000")
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = os.getenv("LOG_LEVEL", "info")

# Process naming
proc_name = "tradovate-dispatch"

# Server mechanics
daemon = False
pidfile = "/tmp/tradovate-dispatch.pid"
umask = 0

# Application
raw_env = [
    "TRADOVATE_API_URL=" + os.getenv("TRADOVATE_API_URL", ""),
    "TRADOVATE_API_KEY=" + os.getenv("TRADOVATE_API_KEY", ""),
    "DISPATCHER_API_KEY=" + os.getenv("DISPATCHER_API_KEY", ""),
    "DATABASE_URL=" + os.getenv("DATABASE_URL", "sqlite:///dispatcher.db"),
]
