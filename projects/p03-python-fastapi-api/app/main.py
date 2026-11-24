"""FastAPI production entrypoint with lifespan events and request tracing."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.middleware import RequestTracingMiddleware
from app.routes import auth, health, items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup phase: Initialize database connections, caches, background workers
    logger.info("Initializing FastAPI microservice resources and connection pools...")
    app.state.startup_complete = True
    yield
    # Shutdown phase: Gracefully terminate connections, flush logs
    logger.info("Gracefully tearing down FastAPI microservice resources...")
    app.state.startup_complete = False


app = FastAPI(
    title="Modular Enterprise Catalog API",
    description="Production-grade FastAPI service featuring Pydantic v2, lifespan context, request tracing, and JWT scopes.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Attach request-tracing middleware
app.add_middleware(RequestTracingMiddleware)

# Mount modular routers under /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
