from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.product import ProductInDB, ProductCreate, ProductUpdate
from app.crud.product import (
    get_product, get_products, create_product_with_image,
    update_product, delete_product, toggle_product_activity,
    update_product_image, get_products_by_category, search_products,
    create_product
)
from app.database import get_db
from app.services.file_storage import file_storage
from app.models.product import Product
from app.crud.stats import get_product_stats, get_category_stats
from app.schema.stats import ProductStats, CategoryStats
from app.core.dependencies import get_current_admin_user, get_current_user
from app.schema.user import UserInDB, UserRole

router = APIRouter(prefix="/products", tags=["products"])

# Публичные эндпоинты
@router.get("/", response_model=List[ProductInDB])
async def read_products(
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список товаров (публичный)"""
    if category:
        return await get_products_by_category(db, category, skip, limit)
    elif search:
        return await search_products(db, search, skip, limit)
    else:
        return await get_products(db, skip, limit)

@router.get("/{product_id}", response_model=ProductInDB)
async def read_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Получить товар по ID (публичный)"""
    product = await get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Админские эндпоинты для управления товарами
@router.post("/admin/", response_model=ProductInDB)
async def create_product_admin(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(0),
    category: str = Form(...),
    sku: Optional[str] = Form(None),
    weight: float = Form(0.0),
    dimensions: Optional[str] = Form(None),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Создать новый товар (только для админов)"""
    product_data = ProductCreate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category=category,
        sku=sku,
        weight=weight,
        dimensions=dimensions,
        is_active=is_active
    )
    
    if image:
        return await create_product_with_image(db, product_data, image)
    else:
        return await create_product(db, product_data)

@router.put("/admin/{product_id}", response_model=ProductInDB)
async def update_product_admin(
    product_id: uuid.UUID,
    product_update: ProductUpdate,  # Принимаем как JSON тело
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Обновить данные товара (только для админов)"""
    updated_product = await update_product(db, product_id, product_update)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.patch("/admin/{product_id}/image", response_model=ProductInDB)
async def update_product_image_admin(
    product_id: uuid.UUID,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Обновить изображение товара (только для админов)"""
    updated_product = await update_product_image(db, product_id, image)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.patch("/admin/{product_id}/image", response_model=ProductInDB)
async def update_product_image_admin(
    product_id: uuid.UUID,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Обновить изображение товара (только для админов)"""
    updated_product = await update_product_image(db, product_id, image)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.patch("/admin/{product_id}/toggle-active", response_model=ProductInDB)
async def toggle_product_active_admin(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Переключить активность товара (только для админов)"""
    updated_product = await toggle_product_activity(db, product_id)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/admin/{product_id}")
async def delete_product_admin(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Удалить товар (только для админов)"""
    success = await delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@router.get("/admin/all", response_model=List[ProductInDB])
async def get_all_products_admin(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Получить все товары включая неактивные (только для админов)"""
    from sqlalchemy import select
    
    if include_inactive:
        result = await db.execute(select(Product).offset(skip).limit(limit))
    else:
        result = await db.execute(
            select(Product)
            .filter(Product.is_active == True)
            .offset(skip)
            .limit(limit)
        )
    
    products = result.scalars().all()
    return [await _add_image_url_to_product(product) for product in products]

# Эндпоинты для статистики
@router.get("/admin/stats/products", response_model=ProductStats)
async def get_products_stats_admin(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Получить статистику по товарам (только для админов)"""
    return await get_product_stats(db)

@router.get("/admin/stats/categories", response_model=List[CategoryStats])
async def get_categories_stats_admin(
    db: AsyncSession = Depends(get_db),
    current_user: UserInDB = Depends(get_current_admin_user)
):
    """Получить статистику по категориям (только для админов)"""
    return await get_category_stats(db)

# Вспомогательная функция
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