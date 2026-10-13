"""Application configuration and settings."""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


class Settings(BaseModel):
    """Application settings with environment variable fallback."""

    app_name: str = Field(
        default_factory=lambda: os.getenv("APP_NAME", "CloudOps Enterprise Platform")
    )
    app_env: str = Field(
        default_factory=lambda: os.getenv("APP_ENV", "development")
    )
    app_version: str = Field(
        default_factory=lambda: os.getenv("APP_VERSION", "1.0.0")
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    )
    host: str = Field(
        default_factory=lambda: os.getenv("HOST", "127.0.0.1")
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000"))
    )

    # Storage Settings (local_memory, s3, minio)
    storage_backend: str = Field(
        default_factory=lambda: os.getenv("STORAGE_BACKEND", "local_memory")
    )
    storage_bucket_default: str = Field(
        default_factory=lambda: os.getenv("STORAGE_BUCKET_DEFAULT", "cloudops-artifacts")
    )
    s3_endpoint_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("S3_ENDPOINT_URL")
    )
    aws_access_key_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID")
    )
    aws_secret_access_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    aws_region: str = Field(
        default_factory=lambda: os.getenv("AWS_REGION", "us-east-1")
    )

    # Database Settings (mock, postgres)
    db_backend: str = Field(
        default_factory=lambda: os.getenv("DB_BACKEND", "mock")
    )
    db_host: str = Field(
        default_factory=lambda: os.getenv("DB_HOST", "localhost")
    )
    db_port: int = Field(
        default_factory=lambda: int(os.getenv("DB_PORT", "5432"))
    )
    db_name: str = Field(
        default_factory=lambda: os.getenv("DB_NAME", "cloudops_db")
    )
    db_user: str = Field(
        default_factory=lambda: os.getenv("DB_USER", "cloudops_user")
    )
    db_password: str = Field(
        default_factory=lambda: os.getenv("DB_PASSWORD", "cloudops_secure_pass_local")
    )
    db_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_URL")
    )

    # ML Inference Settings
    ml_backend: str = Field(
        default_factory=lambda: os.getenv("ML_BACKEND", "local_baseline")
    )
    ml_model_version: str = Field(
        default_factory=lambda: os.getenv("ML_MODEL_VERSION", "v1.0")
    )

    # CORS settings
    cors_origins: List[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
