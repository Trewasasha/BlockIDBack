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
from app.schema.user import UserInDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Вынесите кешированную функцию отдельно
@cache(expire=300)  # Кешируем на 5 минут
async def get_cached_user(email: str, db: AsyncSession):
    return await get_user_by_email(db, email=email)

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
    
    # Используем кешированную функцию
    user = await get_cached_user(token_data.email, db)
    if user is None:
        raise credentials_exception
    
    # Убедитесь, что возвращается объект UserInDB, а не словарь
    return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user