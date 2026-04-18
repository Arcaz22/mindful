"""expand knowledge metadata_info

Revision ID: 4d8d5f7d6d3a
Revises: 8ecc3e3233f7
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d8d5f7d6d3a'
down_revision: Union[str, Sequence[str], None] = '8ecc3e3233f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'knowledge_base',
        'metadata_info',
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'knowledge_base',
        'metadata_info',
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
