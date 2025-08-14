from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid

from app.models.user import User
from app.schema.user import UserCreate, UserInDB, UserOAuthCreate
from app.core.hashing import get_password_hash, verify_password

async def get_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserInDB]:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return UserInDB.from_orm(user) if user else None

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserInDB]:
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    return UserInDB.from_orm(user) if user else None

async def create_user(db: AsyncSession, user_create: UserCreate) -> UserInDB:
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserInDB.from_orm(db_user)

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user