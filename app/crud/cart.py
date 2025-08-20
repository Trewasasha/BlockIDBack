from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid
from fastapi import HTTPException

from app.models.cart import CartItem
from app.models.product import Product
from app.schema.cart import CartItemInDB, CartItemCreate, CartItemUpdate
from app.services.file_storage import file_storage

async def _add_image_url_to_product(product: Product) -> Optional[dict]:
    """Вспомогательная функция для добавления URL изображения к продукту"""
    if not product:
        return None
    
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "is_active": product.is_active,
        "category": product.category,
        "image_object_name": product.image_object_name,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "image_url": file_storage.get_image_url(product.image_object_name) if product.image_object_name else None
    }

async def get_cart_items(db: AsyncSession, user_id: uuid.UUID) -> List[CartItemInDB]:
    """Получить все элементы корзины пользователя с данными о товарах"""
    try:
        result = await db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .filter(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()
        
        result_items = []
        for item in cart_items:
            product_data = await _add_image_url_to_product(item.product) if item.product else None
            
            cart_item_data = {
                "id": item.id,
                "user_id": item.user_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "product": product_data
            }
            result_items.append(CartItemInDB(**cart_item_data))
        
        return result_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cart items: {str(e)}")

async def get_cart_item(db: AsyncSession, cart_item_id: uuid.UUID) -> Optional[CartItemInDB]:
    """Получить конкретный элемент корзины по ID"""
    try:
        result = await db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .filter(CartItem.id == cart_item_id)
        )
        item = result.scalars().first()
        
        if not item:
            return None
        
        product_data = await _add_image_url_to_product(item.product) if item.product else None
        
        return CartItemInDB(
            id=item.id,
            user_id=item.user_id,
            product_id=item.product_id,
            quantity=item.quantity,
            product=product_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cart item: {str(e)}")

async def add_to_cart(db: AsyncSession, user_id: uuid.UUID, cart_item: CartItemCreate) -> CartItemInDB:
    """Добавить товар в корзину или увеличить количество если уже существует"""
    try:
        # Проверяем существование продукта
        product_result = await db.execute(
            select(Product).filter(Product.id == cart_item.product_id)
        )
        product = product_result.scalars().first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if not product.is_active:
            raise HTTPException(status_code=400, detail="Product is not active")
        
        if product.stock < cart_item.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock available")
        
        # Проверяем, есть ли уже такой товар в корзине
        result = await db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .filter(CartItem.user_id == user_id, CartItem.product_id == cart_item.product_id)
        )
        existing_item = result.scalars().first()
        
        if existing_item:
            # Обновляем количество существующего элемента
            new_quantity = existing_item.quantity + cart_item.quantity
            
            if product.stock < new_quantity:
                raise HTTPException(status_code=400, detail="Not enough stock available")
            
            existing_item.quantity = new_quantity
            await db.commit()
            await db.refresh(existing_item)
            
            # Загружаем обновленные данные продукта
            await db.refresh(existing_item, ['product'])
            product_data = await _add_image_url_to_product(existing_item.product)
            
            return CartItemInDB(
                id=existing_item.id,
                user_id=existing_item.user_id,
                product_id=existing_item.product_id,
                quantity=existing_item.quantity,
                product=product_data
            )
        else:
            # Создаем новый элемент корзины
            db_item = CartItem(
                user_id=user_id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity
            )
            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)
            
            # Загружаем данные продукта
            await db.refresh(db_item, ['product'])
            product_data = await _add_image_url_to_product(db_item.product)
            
            return CartItemInDB(
                id=db_item.id,
                user_id=db_item.user_id,
                product_id=db_item.product_id,
                quantity=db_item.quantity,
                product=product_data
            )
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding to cart: {str(e)}")

async def update_cart_item(db: AsyncSession, cart_item_id: uuid.UUID, cart_item: CartItemUpdate) -> Optional[CartItemInDB]:
    """Обновить количество товара в корзине"""
    try:
        result = await db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .filter(CartItem.id == cart_item_id)
        )
        db_item = result.scalars().first()
        
        if not db_item:
            return None
        
        # Проверяем доступное количество на складе
        if db_item.product and cart_item.quantity is not None:
            if db_item.product.stock < cart_item.quantity:
                raise HTTPException(status_code=400, detail="Not enough stock available")
            
            if cart_item.quantity <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be at least 1")
        
        # Обновляем поля
        update_data = cart_item.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        await db.commit()
        await db.refresh(db_item)
        
        # Загружаем обновленные данные продукта
        await db.refresh(db_item, ['product'])
        product_data = await _add_image_url_to_product(db_item.product)
        
        return CartItemInDB(
            id=db_item.id,
            user_id=db_item.user_id,
            product_id=db_item.product_id,
            quantity=db_item.quantity,
            product=product_data
        )
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating cart item: {str(e)}")

async def remove_from_cart(db: AsyncSession, cart_item_id: uuid.UUID) -> bool:
    """Удалить товар из корзины"""
    try:
        result = await db.execute(
            select(CartItem).filter(CartItem.id == cart_item_id)
        )
        db_item = result.scalars().first()
        
        if not db_item:
            return False
        
        await db.delete(db_item)
        await db.commit()
        return True
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing from cart: {str(e)}")

async def clear_cart(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Очистить всю корзину пользователя"""
    try:
        result = await db.execute(
            select(CartItem).filter(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()
        
        for item in cart_items:
            await db.delete(item)
        
        await db.commit()
        return True
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing cart: {str(e)}")

async def get_cart_items_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Получить общее количество товаров в корзине"""
    try:
        from sqlalchemy import func
        
        result = await db.execute(
            select(func.sum(CartItem.quantity))
            .filter(CartItem.user_id == user_id)
        )
        count = result.scalar() or 0
        return count
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cart count: {str(e)}")