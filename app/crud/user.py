from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid

from app.models.user import User
from app.schema.user import UserCreate, UserUpdate, UserInDB, UserOAuthCreate
from app.core.hashing import get_password_hash, verify_password

async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserInDB]:
    """Получить пользователя по ID"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return UserInDB.from_orm(user) if user else None

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserInDB]:
    """Получить пользователя по email"""
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    return UserInDB.from_orm(user) if user else None

async def get_user_by_oauth_id(
    db: AsyncSession, 
    provider: str, 
    provider_id: str
) -> Optional[UserInDB]:
    """Получить пользователя по OAuth ID (vk_id или google_id)"""
    if provider == "vk":
        result = await db.execute(select(User).filter(User.vk_id == provider_id))
    elif provider == "google":
        result = await db.execute(select(User).filter(User.google_id == provider_id))
    else:
        return None
    user = result.scalars().first()
    return UserInDB.from_orm(user) if user else None

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserInDB]:
    """Получить список пользователей с пагинацией"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return [UserInDB.from_orm(user) for user in users]

async def create_user(db: AsyncSession, user_create: UserCreate) -> UserInDB:
    """Создать нового пользователя (обычная регистрация)"""
    if user_create.password != user_create.confirm_password:
        raise ValueError("Passwords do not match")
    
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        is_active=True,
        vk_id=None,
        google_id=None
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserInDB.from_orm(db_user)

async def create_oauth_user(
    db: AsyncSession, 
    user_data: UserOAuthCreate
) -> UserInDB:
    """Создать пользователя через OAuth"""
    db_user = User(
        email=user_data.email,
        hashed_password=None,  # Пароль не требуется для OAuth
        is_active=True,
        avatar=user_data.avatar,
        vk_id=str(user_data.provider_id) if user_data.provider == "vk" else None,
        google_id=str(user_data.provider_id) if user_data.provider == "google" else None
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserInDB.from_orm(db_user)

async def update_user(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    user_update: UserUpdate
) -> Optional[UserInDB]:
    """Обновить данные пользователя"""
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserInDB.from_orm(db_user)

async def authenticate_user(
    db: AsyncSession, 
    email: str, 
    password: str
) -> Optional[UserInDB]:
    """Аутентификация пользователя"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Удалить пользователя"""
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    
    if not db_user:
        return False
    
    await db.delete(db_user)
    await db.commit()
    return True