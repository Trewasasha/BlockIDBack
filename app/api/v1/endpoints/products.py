from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.product import ProductInDB, ProductCreate
from app.crud.product import (
    get_product, get_products, create_product_with_image,
)
from app.database import get_db
from app.services.file_storage import file_storage
from app.models.product import Product

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductInDB)
async def create_product(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(0),
    category: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    product_data = ProductCreate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category=category
    )
    return await create_product_with_image(db, product_data, image)

@router.get("/", response_model=List[ProductInDB])
async def read_products(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await get_products(db, skip=skip, limit=limit)

@router.get("/{product_id}", response_model=ProductInDB)
async def read_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/debug/test", include_in_schema=False)
async def test_products(db: AsyncSession = Depends(get_db)):
    """Тестовый эндпоинт для диагностики"""
    from sqlalchemy import select
    
    # 1. Проверка сырых данных из БД
    result = await db.execute(select(Product))
    raw_products = result.scalars().all()
    
    # 2. Проверка преобразования
    test_products = []
    for product in raw_products[:2]:  # Первые 2 продукта
        try:
            product_dict = {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "is_active": product.is_active,
                "category": product.category,
                "image_object_name": product.image_object_name,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
            test_products.append(product_dict)
        except Exception as e:
            test_products.append({"error": str(e), "product_id": str(product.id)})
    
    return {
        "raw_count": len(raw_products),
        "test_products": test_products
    }