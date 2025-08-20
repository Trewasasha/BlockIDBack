import logging
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid
from app.models.product import Product
from app.schema.product import ProductInDB, ProductCreate
from app.services.file_storage import file_storage

async def create_product_with_image(
    db: AsyncSession, 
    product: ProductCreate, 
    image_file: Optional[UploadFile] = None
) -> ProductInDB:
    # Исключаем поля, которых нет в модели Product
    product_data = product.dict(exclude={"image_url"})
    db_product = Product(**product_data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    if image_file:
        try:
            object_name = await file_storage.upload_image(image_file, db_product.id)
            db_product.image_object_name = object_name
            await db.commit()
            await db.refresh(db_product)
        except Exception as e:
            # Если загрузка изображения не удалась, удаляем продукт
            await db.delete(db_product)
            await db.commit()
            raise e
    
    return await _add_image_url_to_product(db_product)

async def _add_image_url_to_product(product: Product) -> ProductInDB:
    product_dict = {
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
    return ProductInDB(**product_dict)

async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Optional[ProductInDB]:
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalars().first()
    if product:
        return await _add_image_url_to_product(product)
    return None

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ProductInDB]:
    result = await db.execute(select(Product).offset(skip).limit(limit))
    products = result.scalars().all()
    
    print(f"DEBUG: Found {len(products)} products in database")  # Добавьте для отладки
    
    result_products = []
    for product in products:
        try:
            product_with_image = await _add_image_url_to_product(product)
            result_products.append(product_with_image)
        except Exception as e:
            print(f"Error processing product {product.id}: {e}")
            # В случае ошибки возвращаем продукт без image_url
            result_products.append(ProductInDB(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                stock=product.stock,
                is_active=product.is_active,
                category=product.category,
                image_object_name=product.image_object_name,
                created_at=product.created_at,
                updated_at=product.updated_at,
                image_url=None
            ))
    
    print(f"DEBUG: Returning {len(result_products)} processed products")  # Добавьте для отладки
    return result_products