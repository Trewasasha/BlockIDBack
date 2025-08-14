from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    avatar = Column(String, nullable=True)

    # OAuth fields
    vk_id = Column(String, nullable=True, unique=True)
    google_id = Column(String, nullable=True, unique=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"