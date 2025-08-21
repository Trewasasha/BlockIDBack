from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from app.core.config import settings

Base = declarative_base()


engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),  
    echo=True,
    future=True,
    poolclass=NullPool
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session