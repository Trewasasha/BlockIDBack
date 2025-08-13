from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.crud.user import get_user_by_email
from app.database import get_db
from app.schema.user import UserInDB
from app.schema.token import TokenPair

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(
    data: dict, 
    expires_delta: timedelta | None = None
) -> str:
    """Создает access токен (альтернатива create_tokens)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Проверяет, активен ли пользователь"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def create_tokens(
    data: dict,
    expires_delta: timedelta | None = None,
    refresh_expires_delta: timedelta | None = None
) -> TokenPair:
    """Создает пару access и refresh токенов"""
    to_encode = data.copy()
    
    # Access token
    access_expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": access_expire, "type": "access"})
    access_token = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    # Refresh token
    refresh_expire = datetime.utcnow() + (
        refresh_expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": refresh_expire, "type": "refresh"})
    refresh_token = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return TokenPair(access_token=access_token, refresh_token=refresh_token)