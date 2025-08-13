from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from fastapi_cache.decorator import cache
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import create_access_token, create_tokens, get_current_user
from app.crud.user import authenticate_user, get_user_by_email, create_user
from app.schema.token import Token
from app.schema.user import UserCreate, UserInDB
from app.database import get_db

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/auth/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Обрабатывает как JSON, так и form-data"""
    content_type = request.headers.get('content-type')
    
    if content_type == 'application/json':
        data = await request.json()
        email = data.get('email') or data.get('username')
        password = data.get('password')
    else:
        form_data = await request.form()
        email = form_data.get('username')
        password = form_data.get('password')
    
    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login-form", response_model=Token, include_in_schema=False)
async def login_form(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Альтернативный endpoint для form-data авторизации"""
    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserInDB)
async def register(
    user_data: UserCreate,  
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя"""
    # Проверка совпадения паролей (уже есть в UserCreate validator)
    
    # Проверка длины пароля
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    # Проверка существующего пользователя
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Создание пользователя
    return await create_user(db, user_data)

@router.get("/me", response_model=UserInDB)
@cache(expire=60)
async def read_users_me(
    current_user: UserInDB = Depends(get_current_user)
):
    return current_user

@router.get("/auth/check")
async def check_token(
    current_user: UserInDB = Depends(get_current_user)
):
    return {"status": "valid"}

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}