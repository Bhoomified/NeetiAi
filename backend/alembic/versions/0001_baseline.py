"""baseline: the schema as it exists in Supabase on 2026-10-14

Reproduces exactly what create_all() left in production (read from
information_schema/pg_indexes): no foreign keys, a non-unique index on
user.supabase_uid, naive timestamps. Production is *stamped* at this revision
(alembic stamp 0001_baseline), never upgraded through it; a fresh database
runs it and then 0002 like everything else.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _id():
    return sa.Column("id", sa.Integer(), primary_key=True)


def upgrade() -> None:
    op.create_table(
        "user",
        _id(),
        sa.Column("uuid", sa.String(), nullable=False),
        sa.Column("supabase_uid", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("uuid", name="user_uuid_key"),
        sa.UniqueConstraint("email", name="user_email_key"),
    )
    op.create_index("ix_user_supabase_uid", "user", ["supabase_uid"], unique=False)

    op.create_table(
        "transaction",
        _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("merchant_raw", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "budget",
        _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("monthly_limit", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "chatlog",
        _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "investmentwatchlist",
        _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "modelmetadata",
        _id(),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("trained_at", sa.DateTime(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
    )
    op.create_table(
        "incomesource",
        _id(),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # Only ever reached on a scratch database: production is stamped, not upgraded, to this revision.
    for table in ("incomesource", "modelmetadata", "investmentwatchlist", "chatlog", "budget", "transaction"):
        op.drop_table(table)
    op.drop_index("ix_user_supabase_uid", table_name="user")
    op.drop_table("user")
