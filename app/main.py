from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis

from app.core.config import settings
from app.api.v1.endpoints import auth, users


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Auth Service API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1} 
)

@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    redis_client = redis.from_url(str(settings.REDIS_URI))
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Включение роутеров
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)

# Кастомная OpenAPI схема для Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
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
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi