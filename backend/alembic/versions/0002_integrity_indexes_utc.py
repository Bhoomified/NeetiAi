"""integrity, indexes, UTC timestamps, RLS

- user.supabase_uid: unique (the model always said so; production only had a plain index)
- user_id foreign keys on every per-user table. On Postgres they're added NOT VALID:
  enforced for every new or updated row, but the 6 pre-auth orphan rows found on
  2026-10-14 are left in place instead of failing the migration. After cleaning them
  up, run: ALTER TABLE <t> VALIDATE CONSTRAINT <t>_user_id_fkey;
- Indexes for the per-user queries: transaction(user_id, date), incomesource(user_id),
  chatlog(user_id, created_at), budget(user_id); unique watchlist (user_id, symbol)
- Timestamps become timestamptz. Existing values were written with utcnow(), so they
  are reinterpreted AT TIME ZONE 'UTC' — the instant each row describes doesn't change.
- Row Level Security on every table (replaces migrations/manual/0001_enable_rls.sql;
  re-enabling is a no-op if that was already run).

Revision ID: 0002_integrity_indexes_utc
Revises: 0001_baseline
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_integrity_indexes_utc"
down_revision: Union[str, Sequence[str], None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_TABLES = ("transaction", "budget", "chatlog", "investmentwatchlist", "incomesource")
TIMESTAMPS = {
    "user": ["created_at"],
    "transaction": ["date", "created_at"],
    "budget": ["created_at"],
    "chatlog": ["created_at"],
    "investmentwatchlist": ["created_at"],
    "modelmetadata": ["trained_at"],
    "incomesource": ["created_at"],
}
ALL_TABLES = tuple(TIMESTAMPS) + ("alembic_version",)


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.drop_index("ix_user_supabase_uid", table_name="user")
    op.create_index("ix_user_supabase_uid", "user", ["supabase_uid"], unique=True)

    for table in USER_TABLES:
        if _is_postgres():
            op.execute(f'ALTER TABLE "{table}" ADD CONSTRAINT {table}_user_id_fkey '
                       f'FOREIGN KEY (user_id) REFERENCES "user" (id) NOT VALID')
        else:
            with op.batch_alter_table(table) as batch:
                batch.create_foreign_key(f"{table}_user_id_fkey", "user", ["user_id"], ["id"])

    op.create_index("ix_transaction_user_id_date", "transaction", ["user_id", "date"])
    op.create_index("ix_incomesource_user_id", "incomesource", ["user_id"])
    op.create_index("ix_chatlog_user_id_created_at", "chatlog", ["user_id", "created_at"])
    op.create_index("ix_budget_user_id", "budget", ["user_id"])
    with op.batch_alter_table("investmentwatchlist") as batch:
        batch.create_unique_constraint("uq_investmentwatchlist_user_id_symbol", ["user_id", "symbol"])

    if _is_postgres():
        # SQLite has no timezone-aware column type; the app treats its naive values as UTC
        for table, columns in TIMESTAMPS.items():
            for column in columns:
                op.alter_column(
                    table, column,
                    type_=sa.DateTime(timezone=True), existing_type=sa.DateTime(), existing_nullable=False,
                    postgresql_using=f"\"{column}\" AT TIME ZONE 'UTC'",
                )
        for table in ALL_TABLES:
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    # RLS is deliberately left enabled: turning it off would re-expose every table to the anon key.
    if _is_postgres():
        for table, columns in TIMESTAMPS.items():
            for column in columns:
                op.alter_column(
                    table, column,
                    type_=sa.DateTime(), existing_type=sa.DateTime(timezone=True), existing_nullable=False,
                    postgresql_using=f"\"{column}\" AT TIME ZONE 'UTC'",
                )

    with op.batch_alter_table("investmentwatchlist") as batch:
        batch.drop_constraint("uq_investmentwatchlist_user_id_symbol", type_="unique")
    op.drop_index("ix_budget_user_id", table_name="budget")
    op.drop_index("ix_chatlog_user_id_created_at", table_name="chatlog")
    op.drop_index("ix_incomesource_user_id", table_name="incomesource")
    op.drop_index("ix_transaction_user_id_date", table_name="transaction")

    for table in USER_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(f"{table}_user_id_fkey", type_="foreignkey")

    op.drop_index("ix_user_supabase_uid", table_name="user")
    op.create_index("ix_user_supabase_uid", "user", ["supabase_uid"], unique=False)
