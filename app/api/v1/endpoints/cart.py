from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid

from app.schema.cart import CartItemInDB, CartItemCreate, CartItemUpdate
from app.crud.cart import (
    get_cart_items, add_to_cart, update_cart_item, 
    remove_from_cart, clear_cart, get_cart_items_count
)
from app.database import get_db

from app.schema.user import UserInDB
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/", response_model=List[CartItemInDB])
async def read_user_cart(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить корзину текущего пользователя"""
    return await get_cart_items(db, current_user.id)

@router.get("/count")
async def get_cart_count(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить общее количество товаров в корзине"""
    count = await get_cart_items_count(db, current_user.id)
    return {"count": count}

@router.post("/", response_model=CartItemInDB)
async def add_item_to_cart(
    cart_item: CartItemCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавить товар в корзину"""
    return await add_to_cart(db, current_user.id, cart_item)

@router.put("/{cart_item_id}", response_model=CartItemInDB)
async def update_cart_item_quantity(
    cart_item_id: uuid.UUID,
    cart_item: CartItemUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Изменить количество товара в корзине"""
    updated_item = await update_cart_item(db, cart_item_id, cart_item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return updated_item

@router.delete("/{cart_item_id}")
async def remove_item_from_cart(
    cart_item_id: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить товар из корзины"""
    success = await remove_from_cart(db, cart_item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Item removed from cart successfully"}

@router.delete("/")
async def clear_user_cart(
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Очистить всю корзину пользователя"""
    success = await clear_cart(db, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="No items in cart")
    return {"message": "Cart cleared successfully"}