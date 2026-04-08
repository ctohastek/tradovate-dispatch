#!/usr/bin/env python
"""
Tradovate Dispatch Entry Point

Run with: python run.py
Or: gunicorn -c gunicorn.conf.py run:app
"""
import uvicorn
import os
from pathlib import Path

# Setup logging directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("ENV") == "development",
        log_level=os.getenv("LOG_LEVEL", "info")
    )
