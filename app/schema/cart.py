from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.schema.product import ProductInDB

class CartItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(1, ge=1)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=1)

class CartItemInDB(CartItemBase):
    id: UUID
    user_id: UUID
    product: Optional[ProductInDB] = None

    class Config:
        from_attributes = True