"""
Database connection management for PostgreSQL, Qdrant, and Redis.
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import redis.asyncio as redis

from app.config import settings

# Logging
logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database engines and sessions
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.ENVIRONMENT == "development",
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Qdrant client
qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client instance."""
    global qdrant_client
    if qdrant_client is None:
        qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            timeout=30,
        )
    return qdrant_client


async def init_qdrant_collection():
    """Initialize Qdrant collection with proper configuration."""
    client = get_qdrant_client()

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]

        if settings.QDRANT_COLLECTION not in collection_names:
            logger.info(f"Creating Qdrant collection: {settings.QDRANT_COLLECTION}")
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=settings.QDRANT_VECTOR_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Qdrant collection created successfully")
        else:
            logger.info(f"Qdrant collection already exists: {settings.QDRANT_COLLECTION}")
    except Exception as e:
        logger.error(f"Error initializing Qdrant collection: {e}")
        raise


# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_pool() -> redis.ConnectionPool:
    """Get or create Redis connection pool."""
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.REDIS_CONNECTION_POOL_SIZE,
            decode_responses=True,
        )
    return redis_pool


async def get_redis() -> redis.Redis:
    """Get Redis client from connection pool."""
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)


# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.
    Ensures proper session lifecycle management.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database tables."""
    try:
        async with async_engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import (
                camera,
                frame,
                frame_analysis,
                person_track,
                threat_signature,
                threat_detection,
                search_query,
                audit_log,
            )

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_database_connections():
    """Close all database connections gracefully."""
    global qdrant_client, redis_pool

    # Close PostgreSQL engine
    await async_engine.dispose()
    logger.info("PostgreSQL connections closed")

    # Close Qdrant client
    if qdrant_client:
        qdrant_client.close()
        qdrant_client = None
        logger.info("Qdrant client closed")

    # Close Redis pool
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None
        logger.info("Redis connections closed")


# Health check functions
async def check_postgres_health() -> bool:
    """Check PostgreSQL connection health."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False


async def check_qdrant_health() -> bool:
    """Check Qdrant connection health."""
    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return False


async def check_redis_health() -> bool:
    """Check Redis connection health."""
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
