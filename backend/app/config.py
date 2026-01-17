"""
Configuration management for Sentinel Vision platform.
Loads settings from environment variables with validation.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = Field(default="Sentinel Vision Phase 2")
    APP_VERSION: str = Field(default="1.0.0")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")
    ENVIRONMENT: str = Field(default="development")

    # Gemini API
    GEMINI_API_KEY: str
    GEMINI_3_PRO_MODEL: str = Field(default="gemini-3-pro-preview")
    GEMINI_FLASH_MODEL: str = Field(default="gemini-1.5-flash")
    GEMINI_EMBEDDING_MODEL: str = Field(default="text-embedding-005")
    GEMINI_THINKING_LEVEL: str = Field(default="high")
    GEMINI_MEDIA_RESOLUTION: str = Field(default="high")

    # PostgreSQL
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="sentinel_vision")
    POSTGRES_USER: str = Field(default="sentinel_user")
    POSTGRES_PASSWORD: str

    # Qdrant
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION: str = Field(default="frame_embeddings")
    QDRANT_VECTOR_DIM: int = Field(default=768)

    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # Video Processing
    MAX_CAMERAS: int = Field(default=32)
    FRAME_EXTRACTION_FPS: int = Field(default=1)
    MOTION_DETECTION_FPS: int = Field(default=5)
    FRAME_BUFFER_SIZE: int = Field(default=300)
    VIDEO_STORAGE_PATH: str = Field(default="/data/videos")
    FRAME_STORAGE_PATH: str = Field(default="/data/frames")
    THUMBNAIL_STORAGE_PATH: str = Field(default="/data/thumbnails")

    # Person Tracking
    TRACK_TTL_SECONDS: int = Field(default=300)
    TRACK_CONFIDENCE_THRESHOLD: float = Field(default=0.60)
    APPEARANCE_MATCH_THRESHOLD: float = Field(default=0.65)

    # Threat Detection
    ALERT_HIGH_SEVERITY_THRESHOLD: float = Field(default=0.75)
    ALERT_MEDIUM_SEVERITY_THRESHOLD: float = Field(default=0.60)
    CUSTOM_SIGNATURE_ENABLED: bool = Field(default=True)

    # Search
    SEARCH_DEFAULT_LIMIT: int = Field(default=20)
    SEARCH_CANDIDATE_MULTIPLIER: int = Field(default=3)
    SEARCH_MIN_CONFIDENCE: float = Field(default=0.40)

    # Performance
    WORKER_PROCESSES: int = Field(default=4)
    MAX_CONCURRENT_FRAMES: int = Field(default=50)
    API_REQUEST_TIMEOUT: int = Field(default=30)
    DATABASE_POOL_SIZE: int = Field(default=20)
    REDIS_CONNECTION_POOL_SIZE: int = Field(default=10)

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)
    HEALTH_CHECK_INTERVAL: int = Field(default=30)

    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:5173")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)

    # JWT (for future authentication)
    JWT_SECRET_KEY: str = Field(default="change_this_secret_key")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=1440)

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Construct synchronous PostgreSQL database URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
