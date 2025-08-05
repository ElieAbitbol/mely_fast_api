# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Data Correction API"
    debug: bool = False
    environment: str = "production"
    
    # LLM Configuration
    gemini_api_key: Optional[str] = None
    
    # Docker configuration (optional)
    docker_username: Optional[str] = None
    port: Optional[str] = "8000"
    image_name: Optional[str] = "fastapi-image"
    container_name: Optional[str] = "fastapi-container"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields


settings = Settings()
