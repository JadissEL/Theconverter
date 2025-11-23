# Uvicorn configuration for large file uploads
import os

# Worker configuration
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout settings (10 minutes)
timeout = 600
keepalive = 600

# Connection limits
limit_concurrency = 100
backlog = 2048

# Request size limits (500MB)
limit_max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
