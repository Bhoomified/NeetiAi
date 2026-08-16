from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    name: str
    email: str = Field(unique=True)
    monthly_income: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    merchant_raw: str
    amount: float
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    category: str
    monthly_limit: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    role: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestmentWatchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    symbol: str
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str
    version: str
    trained_at: datetime = Field(default_factory=datetime.utcnow)
    accuracy: Optional[float] = None