"""
Alembic environment for NeetiAi.

Connects with the app's own engine (DATABASE_URL from backend/.env), so a
pooler URL or a password containing '%' needs no extra escaping here.
Run from backend/:  venv/bin/alembic upgrade head
"""
from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

from app.database import engine
import app.models  # noqa: F401  registers every table on SQLModel.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Emits SQL to stdout (alembic upgrade head --sql) instead of executing it."""
    context.configure(
        dialect_name=engine.dialect.name,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=engine.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",  # SQLite can't ALTER constraints in place
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
