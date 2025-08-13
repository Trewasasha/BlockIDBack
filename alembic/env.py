from logging.config import fileConfig
from alembic import context
import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Добавляем путь к проекту
sys.path.append(os.getcwd())

from app.core.config import settings
from app.database import Base
from app.models.user import User  # Явно импортируем модель

config = context.config
fileConfig(config.config_file_name)

# Важно: импорт моделей должен быть ДО установки target_metadata
target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Run migrations in 'online' mode with async engine."""
    connectable = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        poolclass=NullPool
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = settings.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())