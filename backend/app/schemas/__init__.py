from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: str


class UserRead(BaseModel):
    id: int
    uuid: str
    name: str
    email: str


class TransactionCreate(BaseModel):
    user_id: int
    merchant_raw: str
    amount: float


class TransactionRead(BaseModel):
    id: int
    user_id: int
    merchant_raw: str
    amount: float
    category: Optional[str]
    confidence_score: Optional[float]   # NEW
    date: datetime