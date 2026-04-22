"""
Application Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "MenoSmooth"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8004
    API_PREFIX: str = "/api/v1"

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://proletson.cn",
    ]

    DATABASE_URL: str = "postgresql://runrunli:runrunli_password@localhost:5432/menopause"

    REDIS_URL: str = "redis://localhost:6379/1"

    JWT_SECRET_KEY: str = "meno-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Qwen AI (DashScope)
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen3.5-plus"
    QWEN_BASE_URL: str = "https://coding.dashscope.aliyuncs.com/v1"

    # Vision (Qwen VL for OCR)
    VISION_API_KEY: str = ""
    VISION_MODEL: str = "qwen-vl-max-latest"
    VISION_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # SMS
    SMS_PROVIDER: str = "aliyun"
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = ""
    ALIYUN_SMS_TEMPLATE_CODE: str = ""

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
