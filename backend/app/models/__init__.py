from sqlmodel import SQLModel, Field  # pyright: ignore[reportMissingImports]
from sqlalchemy import DateTime, Index, UniqueConstraint
from typing import Optional
from datetime import datetime, timezone
import uuid

# Schema changes go through Alembic (backend/alembic/versions), not create_all.


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """Postgres timestamptz comes back aware but in the *session* time zone; SQLite (tests/dev)
    and pre-migration rows come back naive. Every stored value is UTC, so treat naive as UTC
    and convert aware values to UTC, making them comparable and serializing as +00:00."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def UtcTimestamp(**kwargs):
    """Timezone-aware timestamp column (timestamptz on Postgres), defaulting to now in UTC."""
    return Field(default_factory=utcnow, sa_type=DateTime(timezone=True), nullable=False, **kwargs)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    supabase_uid: Optional[str] = Field(default=None, unique=True, index=True)  # NEW — links to Supabase Auth
    name: str
    email: str = Field(unique=True)
    created_at: datetime = UtcTimestamp()

class Transaction(SQLModel, table=True):
    __table_args__ = (Index("ix_transaction_user_id_date", "user_id", "date"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    merchant_raw: str
    amount: float
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    date: datetime = UtcTimestamp()
    created_at: datetime = UtcTimestamp()


class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    category: str
    monthly_limit: float
    created_at: datetime = UtcTimestamp()


class ChatLog(SQLModel, table=True):
    __table_args__ = (Index("ix_chatlog_user_id_created_at", "user_id", "created_at"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    role: str
    message: str
    created_at: datetime = UtcTimestamp()


class InvestmentWatchlist(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_investmentwatchlist_user_id_symbol"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    symbol: str
    note: Optional[str] = None
    created_at: datetime = UtcTimestamp()


class ModelMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str
    version: str
    trained_at: datetime = UtcTimestamp()
    accuracy: Optional[float] = None

class IncomeSource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    label: str                    # e.g. "Part-time tutoring", "Family allowance"
    amount: float
    frequency: str                # "monthly" | "weekly" | "one_time"
    created_at: datetime = UtcTimestamp()
