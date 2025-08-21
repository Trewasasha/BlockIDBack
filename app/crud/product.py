from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from typing import Optional, List
import uuid
from fastapi import HTTPException, UploadFile
from datetime import datetime

from app.models.product import Product
from app.schema.product import ProductInDB, ProductCreate, ProductUpdate
from app.services.file_storage import file_storage

async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Optional[ProductInDB]:
    """Получить товар по ID"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalars().first()
    if product:
        return await _add_image_url_to_product(product)
    return None

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ProductInDB]:
    """Получить список товаров"""
    result = await db.execute(select(Product).offset(skip).limit(limit))
    products = result.scalars().all()
    
    result_products = []
    for product in products:
        try:
            product_with_image = await _add_image_url_to_product(product)
            result_products.append(product_with_image)
        except Exception as e:
            print(f"Error processing product {product.id}: {e}")
            result_products.append(ProductInDB(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                stock=product.stock,
                is_active=product.is_active,
                category=product.category,
                sku=product.sku,
                weight=product.weight,
                dimensions=product.dimensions,
                image_object_name=product.image_object_name,
                created_at=product.created_at,
                updated_at=product.updated_at,
                image_url=None
            ))
    
    return result_products

async def create_product(db: AsyncSession, product: ProductCreate) -> ProductInDB:
    """Создать новый товар (без изображения)"""
    product_data = product.dict(exclude={"image_url"})
    db_product = Product(**product_data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return await _add_image_url_to_product(db_product)

async def create_product_with_image(
    db: AsyncSession, 
    product: ProductCreate, 
    image_file: Optional[UploadFile] = None
) -> ProductInDB:
    """Создать товар с изображением"""
    product_data = product.dict(exclude={"image_url"})
    db_product = Product(**product_data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    if image_file:
        try:
            object_name = await file_storage.upload_image(image_file, db_product.id)
            db_product.image_object_name = object_name
            db_product.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(db_product)
        except Exception as e:
            await db.delete(db_product)
            await db.commit()
            raise e
    
    return await _add_image_url_to_product(db_product)

async def update_product(
    db: AsyncSession, 
    product_id: uuid.UUID, 
    product_update: ProductUpdate
) -> Optional[ProductInDB]:
    """Обновить данные товара"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalars().first()
    
    if not db_product:
        return None
    
    update_data = product_update.dict(exclude_unset=True, exclude={"image_url"})
    
    # Фильтруем None значения для обязательных полей
    for field, value in update_data.items():
        if value is not None:  # Не устанавливаем None значения
            setattr(db_product, field, value)
    
    db_product.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_product)
    return await _add_image_url_to_product(db_product)

async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> bool:
    """Удалить товар"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalars().first()
    
    if not db_product:
        return False
    
    if db_product.image_object_name:
        try:
            await file_storage.delete_image(db_product.image_object_name)
        except Exception as e:
            print(f"Error deleting image from MinIO: {e}")
    
    await db.delete(db_product)
    await db.commit()
    return True

async def toggle_product_activity(db: AsyncSession, product_id: uuid.UUID) -> Optional[ProductInDB]:
    """Переключить активность товара"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalars().first()
    
    if not db_product:
        return None
    
    db_product.is_active = not db_product.is_active
    db_product.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_product)
    return await _add_image_url_to_product(db_product)

async def update_product_image(
    db: AsyncSession, 
    product_id: uuid.UUID, 
    image_file: UploadFile
) -> Optional[ProductInDB]:
    """Обновить изображение товара"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalars().first()
    
    if not db_product:
        return None
    
    # Удаляем старое изображение если оно есть
    if db_product.image_object_name:
        try:
            await file_storage.delete_image(db_product.image_object_name)
        except Exception as e:
            print(f"Error deleting old image: {e}")
    
    try:
        object_name = await file_storage.upload_image(image_file, product_id)
        db_product.image_object_name = object_name
        db_product.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_product)
        return await _add_image_url_to_product(db_product)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")

async def get_products_by_category(
    db: AsyncSession, 
    category: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[ProductInDB]:
    """Получить товары по категории"""
    result = await db.execute(
        select(Product)
        .filter(Product.category == category, Product.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    products = result.scalars().all()
    return [await _add_image_url_to_product(product) for product in products]

async def search_products(
    db: AsyncSession, 
    query: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[ProductInDB]:
    """Поиск товаров по названию и описанию"""
    result = await db.execute(
        select(Product)
        .filter(
            (Product.name.ilike(f"%{query}%")) | 
            (Product.description.ilike(f"%{query}%")),
            Product.is_active == True
        )
        .offset(skip)
        .limit(limit)
    )
    products = result.scalars().all()
    return [await _add_image_url_to_product(product) for product in products]

async def _add_image_url_to_product(product: Product) -> ProductInDB:
    """Добавить URL изображения к данным продукта"""
    product_dict = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "is_active": product.is_active,
        "category": product.category,
        "sku": product.sku,
        "weight": product.weight,
        "dimensions": product.dimensions,
        "image_object_name": product.image_object_name,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "image_url": file_storage.get_image_url(product.image_object_name) if product.image_object_name else None
    }
    return ProductInDB(**product_dict)