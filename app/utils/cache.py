from functools import wraps
from typing import Callable, Optional
from datetime import timedelta
from fastapi import Request, Response
from app.core.config import settings
import redis.asyncio as redis
import pickle

redis_client = redis.from_url(settings.REDIS_URI)

def cache(
    expire: int = 60,
    key_prefix: Optional[str] = None,
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Генерируем ключ для кеша
            cache_key = key_prefix or f"{func.__module__}:{func.__name__}"
            cache_key += f":{str(args)}:{str(kwargs)}"
            
            # Пытаемся получить данные из кеша
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return pickle.loads(cached_data)
            
            # Если данных нет в кеше, выполняем функцию
            response = await func(request, *args, **kwargs)
            
            # Сохраняем результат в кеш
            await redis_client.setex(
                cache_key,
                timedelta(seconds=expire),
                pickle.dumps(response),
            )
            
            return response
        return wrapper
    return decorator