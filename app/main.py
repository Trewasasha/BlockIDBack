from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis.asyncio as redis
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from app.core.config import settings
from app.api.v1.endpoints import auth, users, cart, products
from app.database import get_db
from app.logging_config import setup_logging
from sqlalchemy.ext.asyncio import AsyncSession

setup_logging()

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Управление жизненным циклом приложения"""

    try:
        redis_client = redis.from_url(str(settings.REDIS_URI))
        FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {str(e)}")
        raise
    

    try:
        # Импортируем и инициализируем FileStorage
        from app.services.file_storage import file_storage
        # Просто обращение к file_storage вызовет __init__ который создаст bucket
        logger.info("FileStorage initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FileStorage: {str(e)}")
        # Не прерываем запуск, т.к. приложение может работать без MinIO
        # Но логируем ошибку для диагностики
    
    yield
    
    # Очистка при завершении
    await FastAPICache.clear()
    logger.info("Application shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Auth Service API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True
    },
    lifespan=lifespan
)

@app.get("/health", include_in_schema=False)
@cache(expire=10)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Проверка здоровья сервиса (включая БД)"""
    try:
        # Проверка подключения к БД
        await db.execute("SELECT 1")
        return {
            "status": "ok",
            "database": "connected",
            "redis": "connected" if FastAPICache.get_backend() else "disconnected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Service unavailable: {str(e)}"
        )

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Включение роутеров
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(cart.router, prefix=settings.API_V1_STR)

# Кастомная OpenAPI схема для Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title + " | " + ("DEV" if settings.DEBUG else "PROD"),
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Добавляем поддержку OAuth2 в Swagger UI
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": f"{settings.API_V1_STR}/auth/login",
                    "scopes": {}
                },
                "refreshToken": {
                    "tokenUrl": f"{settings.API_V1_STR}/auth/refresh",
                    "scopes": {}
                }
            }
        }
    }
    
    # Добавляем глобальную безопасность
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )