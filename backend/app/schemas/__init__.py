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

class UserCreate(BaseModel):
    name: str
    email: str
    


class ForecastCategoryPrediction(BaseModel):
    category: str
    predicted_amount: float
    method: str   # "random_forest" or "rolling_average_fallback"


class ForecastRead(BaseModel):
    user_id: int
    weeks_of_history: int
    predicted_total: float
    total_method: str
    categories: list[ForecastCategoryPrediction]


class BudgetOptimizeRequest(BaseModel):
    user_id: int
    savings_target_pct: float          # user-set, e.g. 0.15 for 15% — REQUIRED, no default baked in
    weekly_income: Optional[float] = None   # if omitted, derived from user.monthly_income / 4.33
    category_weights: Optional[dict[str, float]] = None   # optional override of default priorities


class BudgetAllocation(BaseModel):
    category: str
    predicted_amount: float
    budget_cap: float
    cut_percent: float


class BudgetOptimizeResponse(BaseModel):
    weekly_income: float
    savings_target: float
    projected_savings: float
    target_met: bool
    allocations: list[BudgetAllocation]

class RiskQuizRequest(BaseModel):
    age_score: int        # 1-5
    income_stability: int  # 1-5
    investment_horizon: int  # 1-5
    loss_reaction: int      # 1-5
    existing_savings_months: int  # 1-5


class WatchlistCreate(BaseModel):
    user_id: int
    symbol: str          # mfapi.in scheme code, e.g. "119551"
    note: Optional[str] = None


class WatchlistRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    note: Optional[str]

class IncomeSourceCreate(BaseModel):
    user_id: int
    label: str
    amount: float
    frequency: str  # "monthly" | "weekly"


class IncomeSourceRead(BaseModel):
    id: int
    user_id: int
    label: str
    amount: float
    frequency: str


class TotalIncomeRead(BaseModel):
    weekly_income: float
    sources: list[IncomeSourceRead]

class UserSync(BaseModel):
    supabase_uid: str
    email: str
    first_name: str
    last_name: str