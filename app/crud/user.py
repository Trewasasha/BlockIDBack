from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid

from app.models.user import User, UserRole
from app.schema.user import UserCreate, UserInDB, UserOAuthCreate
from app.core.hashing import get_password_hash, verify_password

async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user 

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserInDB]:
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if user:
        # Преобразуем модель SQLAlchemy в Pydantic схему
        user_dict = {
            "id": user.id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "is_active": user.is_active,
            "role": user.role,
            "created_at": user.created_at,
            "avatar": user.avatar,
            "vk_id": user.vk_id,
            "google_id": user.google_id
        }
        return UserInDB(**user_dict)
    return None

async def create_user(db: AsyncSession, user_create: UserCreate) -> UserInDB:
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        role=UserRole(user_create.role.value),
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Возвращаем как UserInDB
    user_dict = {
        "id": db_user.id,
        "email": db_user.email,
        "hashed_password": db_user.hashed_password,
        "is_active": db_user.is_active,
        "role": db_user.role,
        "created_at": db_user.created_at,
        "avatar": db_user.avatar,
        "vk_id": db_user.vk_id,
        "google_id": db_user.google_id
    }
    return UserInDB(**user_dict)

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_users_by_role(db: AsyncSession, role: UserRole) -> List[UserInDB]:
    result = await db.execute(select(User).filter(User.role == role))
    users = result.scalars().all()
    return [UserInDB.from_orm(user) for user in users]