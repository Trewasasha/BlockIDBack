from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pathlib import Path
import uuid
import aiofiles
from fastapi import UploadFile
import os

from app.crud.product import create_product_with_image
from app.models.product import Product
from app.schema.product import ProductCreate
from app.services.file_storage import file_storage

async def init_products(db: AsyncSession, image_dir: str = "initial_images"):
    await file_storage.ensure_bucket_exists()
    
    # Проверяем, есть ли уже продукты
    result = await db.execute(select(Product))
    if result.scalars().first():
        print("Products already exist, skipping initialization")
        return
    
    products_data = [
        {
            "name": "Кухонный гарнитур 'Модерн'",
            "description": "Современный кухонный гарнитур из массива дуба",
            "price": 125000.00,
            "stock": 10,
            "category": "Кухонный гарнитур"
        },
        # ... другие продукты ...
    ]
    
    image_dir_path = Path(image_dir)
    for product_data in products_data:
        image_file = None
        image_path = image_dir_path / f"{product_data['name']}.jpg"
        
        if image_path.exists():
            async with aiofiles.open(image_path, "rb") as f:
                image_content = await f.read()
                image_file = UploadFile(
                    filename=image_path.name,
                    file=image_content,
                    content_type="image/jpeg"
                )
        
        await create_product_with_image(
            db, 
            ProductCreate(**product_data), 
            image_file
        )
    
    print("Initial products created successfully")