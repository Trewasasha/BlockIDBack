from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schema.user import UserInDB 
from app.crud.user import get_user
from app.database import get_db
from app.core.dependencies import get_current_active_user
from uuid import UUID

router = APIRouter(tags=["users"])

@router.get("/users/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user),
):
    if current_user.id != user_id:
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