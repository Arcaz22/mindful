"""add source search cache audit table

Revision ID: 5f7a9e2c1b4d
Revises: 4d8d5f7d6d3a
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5f7a9e2c1b4d"
down_revision: Union[str, Sequence[str], None] = "4d8d5f7d6d3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_search_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query", sa.String(length=500), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=False),
        sa.Column("source_domain", sa.String(length=255), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("response_id", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_search_cache_query", "source_search_cache", ["query"])
    op.create_index("ix_source_search_cache_source_url", "source_search_cache", ["source_url"])
    op.create_index("ix_source_search_cache_source_domain", "source_search_cache", ["source_domain"])
    op.create_index("ix_source_search_cache_retrieved_at", "source_search_cache", ["retrieved_at"])
    op.create_index("ix_source_search_cache_content_hash", "source_search_cache", ["content_hash"])
    op.create_index("ix_source_search_cache_response_id", "source_search_cache", ["response_id"])


def downgrade() -> None:
    op.drop_index("ix_source_search_cache_response_id", table_name="source_search_cache")
    op.drop_index("ix_source_search_cache_content_hash", table_name="source_search_cache")
    op.drop_index("ix_source_search_cache_retrieved_at", table_name="source_search_cache")
    op.drop_index("ix_source_search_cache_source_domain", table_name="source_search_cache")
    op.drop_index("ix_source_search_cache_source_url", table_name="source_search_cache")
    op.drop_index("ix_source_search_cache_query", table_name="source_search_cache")
    op.drop_table("source_search_cache")
