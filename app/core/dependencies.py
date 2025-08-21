from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi_cache.decorator import cache

from app.core.config import settings
from app.crud.user import get_user_by_email
from app.database import get_db
from app.schema.token import TokenData
from app.schema.user import UserInDB, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Кэшированная функция, которая возвращает данные пользователя в виде словаря
@cache(expire=300)
async def get_cached_user_data(email: str, db: AsyncSession) -> Optional[dict]:
    """Получает данные пользователя и кэширует их в виде словаря"""
    user = await get_user_by_email(db, email=email)
    if user:
        return user.to_dict()  # Используем метод to_dict для сериализации
    return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """
    Получает текущего пользователя по JWT токену с кешированием
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Пытаемся получить данные из кэша
    user_data = await get_cached_user_data(token_data.email, db)
    
    if user_data is not None:
        try:
            # Преобразуем словарь обратно в UserInDB
            return UserInDB.from_dict(user_data)
        except Exception as e:
            # Если преобразование не удалось, получаем из базы
            user = await get_user_by_email(db, token_data.email)
            if user is None:
                raise credentials_exception
            return user
    else:
        # Если нет в кэше, получаем из базы
        user = await get_user_by_email(db, token_data.email)
        if user is None:
            raise credentials_exception
        return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Проверяет, что пользователь активен"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_active_user)
) -> UserInDB:
    """Проверяет, что пользователь имеет роль ADMIN"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user