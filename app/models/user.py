from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    avatar = Column(String, nullable=True)

    # OAuth fields
    vk_id = Column(String, nullable=True, unique=True)
    google_id = Column(String, nullable=True, unique=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, is_active={self.is_active})>"
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "is_active": self.is_active,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "avatar": self.avatar,
            "vk_id": self.vk_id,
            "google_id": self.google_id
        }