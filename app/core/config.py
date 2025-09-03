import os
from typing import Any, Dict, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Route Optimization System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A modern, cloud-based route optimization service"
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://ros_user:ros_password@localhost:5432/ros_db"
    TEST_DATABASE_URL: str = "postgresql://ros_user:ros_password@localhost:5432/ros_test_db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External Services
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    MAPBOX_ACCESS_TOKEN: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Environment
    ENVIRONMENT: str = "development"

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql://ros_user:ros_password@localhost:5432/ros_db"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
