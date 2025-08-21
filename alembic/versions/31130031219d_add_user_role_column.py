"""add_user_role_column

Revision ID: 31130031219d
Revises: e625cd8fba92
Create Date: 2025-08-20 18:37:15.401250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '31130031219d'
down_revision: Union[str, Sequence[str], None] = 'e625cd8fba92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем enum тип
    user_role_enum = postgresql.ENUM('USER', 'ADMIN', name='userrole')
    user_role_enum.create(op.get_bind())
    
    # Добавляем колонку role с значением по умолчанию 'user'
    op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='USER'))


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем колонку role
    op.drop_column('users', 'role')
    
    # Удаляем enum тип
    user_role_enum = postgresql.ENUM('user', 'admin', name='userrole')
    user_role_enum.drop(op.get_bind())