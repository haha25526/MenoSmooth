"""
Backstage Configuration
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "更年不期后台"
    DEBUG: bool = True

    ADMIN_PASSWORD: str = os.getenv("BACKSTAGE_ADMIN_PASSWORD", "admin123")

    HOST: str = "0.0.0.0"
    PORT: int = 8005

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://runrunli:runrunli_password@localhost:5432/menopause"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
