"""
Main FastAPI application for Sentinel Vision Phase 2.
Entry point for the security intelligence platform.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import (
    init_database,
    init_qdrant_collection,
    close_database_connections,
    check_postgres_health,
    check_qdrant_health,
    check_redis_health,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes database connections and performs cleanup.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    try:
        # Initialize databases
        logger.info("Initializing PostgreSQL database...")
        await init_database()

        logger.info("Initializing Qdrant vector database...")
        await init_qdrant_collection()

        logger.info("All database connections initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_database_connections()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade enterprise security intelligence platform with natural language video search, threat signature detection, and advanced forensics.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent error response format."""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed error information."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_error",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.ENVIRONMENT == "development" else None,
            }
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """Root endpoint providing API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    Verifies connectivity to all critical services.
    """
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "services": {
            "postgres": {"status": "unknown", "healthy": False},
            "qdrant": {"status": "unknown", "healthy": False},
            "redis": {"status": "unknown", "healthy": False},
        },
    }

    # Check PostgreSQL
    try:
        postgres_healthy = await check_postgres_health()
        health_status["services"]["postgres"] = {
            "status": "healthy" if postgres_healthy else "unhealthy",
            "healthy": postgres_healthy,
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check error: {e}")
        health_status["services"]["postgres"] = {
            "status": "error",
            "healthy": False,
            "error": str(e),
        }

    # Check Qdrant
    try:
        qdrant_healthy = await check_qdrant_health()
        health_status["services"]["qdrant"] = {
            "status": "healthy" if qdrant_healthy else "unhealthy",
            "healthy": qdrant_healthy,
        }
    except Exception as e:
        logger.error(f"Qdrant health check error: {e}")
        health_status["services"]["qdrant"] = {
            "status": "error",
            "healthy": False,
            "error": str(e),
        }

    # Check Redis
    try:
        redis_healthy = await check_redis_health()
        health_status["services"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "healthy": redis_healthy,
        }
    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        health_status["services"]["redis"] = {
            "status": "error",
            "healthy": False,
            "error": str(e),
        }

    # Determine overall health
    all_healthy = all(
        service["healthy"] for service in health_status["services"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "degraded"

    # Add timestamp
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()

    return health_status


# Readiness endpoint
@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 if service is ready to accept traffic.
    """
    health = await health_check()

    if health["status"] == "healthy":
        return {"ready": True, "status": "ready"}
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "status": "not_ready", "health": health},
        )


# Liveness endpoint
@app.get("/live", tags=["Health"])
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if service is alive.
    """
    return {"alive": True, "status": "alive"}


# Import and register API routers
from app.api import cameras, search, threats, tracking

app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["Cameras"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(threats.router, prefix="/api/v1/threats", tags=["Threats"])
app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
