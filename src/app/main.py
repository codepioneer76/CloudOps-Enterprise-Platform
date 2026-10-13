"""FastAPI Application Factory for CloudOps Enterprise Platform."""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.api.router import main_api_router
from app.api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for startup and shutdown routines."""
    # Startup: Initialize services or caches if needed
    yield
    # Shutdown: Clean up resources


def create_app(custom_settings: Optional[Settings] = None) -> FastAPI:
    """Create and configure an instance of the FastAPI application."""
    settings = custom_settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "CloudOps Enterprise Platform: Cloud Infrastructure, Automation & Deployment Ecosystem. "
            "Simulates industry-grade cloud infrastructure and DevOps automation across IaaS, storage, "
            "containers, Kubernetes, serverless, CI/CD, monitoring, streaming, and ML inference."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount top-level /health endpoints directly on root for standard Kubernetes probes
    app.include_router(health_router)

    # Mount versioned API routes under /api/v1
    app.include_router(main_api_router)

    @app.get(
        "/",
        tags=["Root"],
        status_code=status.HTTP_200_OK,
        summary="Platform Root Status",
    )
    def root(current_settings: Settings = Depends(get_settings)):
        return {
            "app_name": current_settings.app_name,
            "version": current_settings.app_version,
            "environment": current_settings.app_env,
            "status": "operational",
            "docs": "/docs",
            "health": "/health",
            "api_v1": "/api/v1",
        }

    return app


# Default ASGI application instance for uvicorn
app = create_app()
