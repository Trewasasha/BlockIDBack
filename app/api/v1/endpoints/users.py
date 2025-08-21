from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schema.user import UserInDB, UserUpdate, UserRole
from app.crud.user import get_user, get_users_by_role
from app.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from uuid import UUID
from typing import List

from app.models.user import User

router = APIRouter(tags=["users"])

@router.get("/users/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user),
):

    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    user = await get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.get("/users", response_model=List[UserInDB])
async def read_users(
    role: UserRole = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user),
):
    """
    Получить список пользователей (только для админов)
    """
    if role:
        return await get_users_by_role(db, role)
    else:
        result = await db.execute(select(User))
        users = result.scalars().all()
        return [UserInDB.from_orm(user) for user in users]

@router.patch("/users/{user_id}", response_model=UserInDB)
async def update_user_role(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user),
):
    """
    Обновить данные пользователя (только для админов)
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    

    if user_update.email:
        user.email = user_update.email
    if user_update.role:
        user.role = user_update.role
    
    await db.commit()
    await db.refresh(user)
    
    return UserInDB.from_orm(user)