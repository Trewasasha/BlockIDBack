from pydantic_settings import BaseSettings
from pydantic import Field, RedisDsn
from typing import List, Optional

class Settings(BaseSettings):
    # Основные настройки
    PROJECT_NAME: str = "Auth Service"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    BACKEND_CORS_ORIGINS: List[str] = ["http://185.135.80.107:5173"]
    
    # Настройки базы данных
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "auth_service"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Настройки Redis
    REDIS_URI: RedisDsn = "redis://redis:6379/0"
    
    # Настройки JWT
    SECRET_KEY: str = Field(default="your-secret-key-here")
    REFRESH_SECRET_KEY: str = Field(default="your-refresh-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_ALGORITHM: str = "HS256"
    
    USE_ASYNC_MIGRATIONS: bool = False
    
    # OAuth провайдеры
    VK_CLIENT_ID: Optional[str] = None
    VK_CLIENT_SECRET: Optional[str] = None
    VK_REDIRECT_URI: Optional[str] = "http://localhost:8000/api/v1/auth/vk/callback"
    
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = "http://localhost:8000/api/v1/auth/google/callback"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

if not settings.SQLALCHEMY_DATABASE_URI:
    settings.SQLALCHEMY_DATABASE_URI = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
    )