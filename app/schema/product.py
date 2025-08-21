from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    category: str = Field(..., max_length=50)
    sku: Optional[str] = Field(None, max_length=50)  # Артикул
    weight: float = Field(0.0, ge=0)  # Вес в кг
    dimensions: Optional[str] = Field(None, max_length=50)  # Размеры
    image_object_name: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    is_active: Optional[bool] = None

class ProductInDB(ProductBase):
    id: UUID  
    is_active: bool
    created_at: datetime
    updated_at: datetime
    image_url: Optional[str] = None 

    class Config:
        from_attributes = True