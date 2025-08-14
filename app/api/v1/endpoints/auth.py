from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_tokens,
    get_current_user,
    validate_refresh_token,
    verify_password
)
from app.crud.user import get_user_by_email, create_user
from app.schema.token import TokenPair
from app.schema.user import UserCreate, UserInDB
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenPair)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return create_tokens({"sub": user.email})

@router.post("/register", response_model=TokenPair)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = await create_user(db, user_data)
    return create_tokens({"sub": user.email})

@router.post("/refresh", response_model=TokenPair)
async def refresh(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    user = await validate_refresh_token(refresh_token, db)
    return create_tokens({"sub": user.email})

@router.get("/me", response_model=UserInDB)
async def read_users_me(
    current_user: UserInDB = Depends(get_current_user)
):
    return current_user