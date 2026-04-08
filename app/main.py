from fastapi import FastAPI
from app.routes import health_router, execute_router

app = FastAPI(
    title="Tradovate Dispatch",
    description="Command dispatcher for Tradovate trading API",
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(execute_router)
