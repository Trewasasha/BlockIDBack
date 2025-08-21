from sqlalchemy import Column, DateTime, String, Float, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    category = Column(String(50), nullable=False)
    image_object_name = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Дополнительные поля для админки
    sku = Column(String(50), unique=True, nullable=True)  # Артикул
    weight = Column(Float, default=0.0)  # Вес в кг
    dimensions = Column(String(50), nullable=True)  # Размеры (например: "10x20x30")

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"