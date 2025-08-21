from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, List
from app.models.product import Product
from app.models.user import User
from app.schema.stats import ProductStats, CategoryStats

async def get_product_stats(db: AsyncSession) -> ProductStats:
    """Получить статистику по товарам"""
    # Общее количество товаров
    total_result = await db.execute(select(func.count(Product.id)))
    total_products = total_result.scalar() or 0
    
    # Активные товары
    active_result = await db.execute(
        select(func.count(Product.id)).filter(Product.is_active == True)
    )
    active_products = active_result.scalar() or 0
    
    # Неактивные товары
    inactive_products = total_products - active_products
    
    # Товары по категориям
    category_result = await db.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
    )
    products_by_category = dict(category_result.all())
    
    # Товары с низким запасом
    low_stock_result = await db.execute(
        select(func.count(Product.id)).filter(Product.stock < 10, Product.is_active == True)
    )
    low_stock_products = low_stock_result.scalar() or 0
    
    return ProductStats(
        total_products=total_products,
        active_products=active_products,
        inactive_products=inactive_products,
        products_by_category=products_by_category,
        low_stock_products=low_stock_products
    )

async def get_category_stats(db: AsyncSession) -> List[CategoryStats]:
    """Получить статистику по категориям"""
    result = await db.execute(
        select(
            Product.category,
            func.count(Product.id).label('product_count'),
            func.sum(Product.stock).label('total_stock')
        )
        .filter(Product.is_active == True)
        .group_by(Product.category)
    )
    
    return [
        CategoryStats(
            category=row[0],
            product_count=row[1],
            total_stock=row[2] or 0
        )
        for row in result.all()
    ]