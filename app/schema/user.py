from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    confirm_password: str = Field(..., description="Password confirmation")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError("Passwords don't match")
        return v

class UserOAuthCreate(BaseModel):
    email: EmailStr
    provider: str  # "vk" или "google"
    provider_id: str
    avatar: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: UUID
    hashed_password: str
    is_active: bool
    created_at: datetime
    avatar: Optional[str] = None
    vk_id: Optional[str] = None
    google_id: Optional[str] = None

    class Config:
        from_attributes = True