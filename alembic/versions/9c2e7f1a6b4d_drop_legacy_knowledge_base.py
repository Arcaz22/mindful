"""drop legacy knowledge base table

Revision ID: 9c2e7f1a6b4d
Revises: 5f7a9e2c1b4d
"""

from typing import Sequence, Union

from alembic import op
import pgvector
import sqlalchemy as sa


revision: str = "9c2e7f1a6b4d"
down_revision: Union[str, Sequence[str], None] = "5f7a9e2c1b4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("knowledge_base")


def downgrade() -> None:
    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=384),
            nullable=False,
        ),
        sa.Column("metadata_info", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
