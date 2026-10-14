from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException
import os
import time
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./neetiai.db")
DB_ECHO = os.getenv("DB_ECHO", "false").lower() in ("1", "true", "yes")
DB_HOST = make_url(DATABASE_URL).host or "local sqlite"
ALEMBIC_INI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini")

if DATABASE_URL.startswith("sqlite"):
    # FastAPI runs sync routes in a threadpool, so SQLite must allow cross-thread use
    engine = create_engine(DATABASE_URL, echo=DB_ECHO, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        pool_pre_ping=True,       # drop connections Supabase/pgbouncer closed while idle
        pool_recycle=300,         # never reuse a connection older than 5 min
        connect_args={"connect_timeout": 5},  # fail fast instead of hanging startup
    )

# How long to wait between reconnect attempts while degraded, so a dead DB
# doesn't add a 5s connect timeout to every single request.
RETRY_SECONDS = 10


class DBState:
    ready: bool = False
    error: str | None = None
    last_attempt: float = 0.0


db_state = DBState()


def describe_db_error(exc: Exception) -> str:
    """Turns a driver error into one actionable line (never includes the password)."""
    raw = str(getattr(exc, "orig", None) or exc).strip()
    msg = raw.splitlines()[0] if raw else repr(exc)
    low = msg.lower()
    if "translate host name" in low or "name or service not known" in low or "nodename nor servname" in low:
        hint = ("DNS lookup failed. Supabase direct hosts (db.<ref>.supabase.co) are IPv6-only; "
                "on an IPv4-only network use the Session pooler string (Dashboard > Connect > Session pooler). "
                "Also check the project isn't paused.")
    elif "timeout" in low or "timed out" in low:
        hint = "Connection timed out: project paused, or the network blocks outbound port 5432/6543."
    elif "password authentication failed" in low:
        hint = "Wrong database password (pooler user must be postgres.<project-ref>)."
    elif "tenant or user not found" in low:
        hint = "Pooler rejected the user: it must be postgres.<project-ref>, copied from Dashboard > Connect."
    else:
        hint = msg
    return f"{DB_HOST}: {hint}"


def migration_status() -> str | None:
    """None when the database is at the latest Alembic revision, else a one-line reason.
    Local SQLite is built by create_all and isn't versioned, so it always counts as current."""
    if engine.dialect.name == "sqlite":
        return None
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    head = ScriptDirectory.from_config(Config(ALEMBIC_INI)).get_current_head()
    with engine.connect() as conn:
        current = MigrationContext.configure(conn).get_current_revision()
    if current == head:
        return None
    if current is None:
        return f"database has no Alembic revision (expected {head}) — see backend/alembic/README.md"
    return f"database is at {current}, code expects {head} — run: venv/bin/alembic upgrade head"


def init_db() -> bool:
    """Checks the connection (and, for local SQLite only, creates tables).
    Returns False (degraded mode) instead of raising.

    Postgres schema changes go through Alembic only — create_all would silently
    create tables that don't match the migrations."""
    db_state.last_attempt = time.monotonic()
    try:
        if engine.dialect.name == "sqlite":
            SQLModel.metadata.create_all(engine)
        else:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
    except OperationalError as e:
        db_state.ready = False
        db_state.error = describe_db_error(e)
        return False
    db_state.ready = True
    db_state.error = None
    return True


def ensure_db() -> bool:
    if db_state.ready:
        return True
    if time.monotonic() - db_state.last_attempt < RETRY_SECONDS:
        return False
    return init_db()


def mark_db_down(exc: Exception):
    db_state.ready = False
    db_state.error = describe_db_error(exc)
    db_state.last_attempt = time.monotonic()


def create_db_and_tables():
    return init_db()


def get_session():
    if not ensure_db():
        raise HTTPException(status_code=503, detail=f"Database unavailable — {db_state.error}")
    with Session(engine) as session:
        yield session
