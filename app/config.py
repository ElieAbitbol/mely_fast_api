# core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "My FastAPI App"
    debug: bool = False
    environment: str = "production"

    class Config:
        env_file = ".env.example"


settings = Settings()
