from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime

class ProductStats(BaseModel):
    total_products: int
    active_products: int
    inactive_products: int
    products_by_category: Dict[str, int]
    low_stock_products: int 

class SystemStats(BaseModel):
    total_users: int
    total_orders: int
    total_revenue: float
    product_stats: ProductStats

class CategoryStats(BaseModel):
    category: str
    product_count: int
    total_stock: int