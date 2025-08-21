from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    confirm_password: str = Field(..., description="Password confirmation")
    role: UserRole = Field(default=UserRole.USER, description="User role")

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
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

class UserInDB(UserBase):
    id: UUID
    hashed_password: str
    is_active: bool
    role: UserRole
    created_at: datetime
    avatar: Optional[str] = None
    vk_id: Optional[str] = None
    google_id: Optional[str] = None

    class Config:
        from_attributes = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь для кэширования"""
        return {
            "id": str(self.id),
            "email": self.email,
            "hashed_password": self.hashed_password,
            "is_active": self.is_active,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "avatar": self.avatar,
            "vk_id": self.vk_id,
            "google_id": self.google_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInDB':
        """Создает объект из словаря (из кэша)"""
        return cls(
            id=UUID(data["id"]),
            email=data["email"],
            hashed_password=data["hashed_password"],
            is_active=data["is_active"],
            role=UserRole(data["role"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            avatar=data.get("avatar"),
            vk_id=data.get("vk_id"),
            google_id=data.get("google_id")
        )