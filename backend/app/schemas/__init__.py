from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Literal, Optional
from datetime import datetime

from app.models import as_utc


# Shared input bounds: positive rupee amounts up to ₹1 crore, short labels
Amount = Annotated[float, Field(gt=0, le=10_000_000)]
QuizScore = Annotated[int, Field(ge=1, le=5)]


class UserRead(BaseModel):
    id: int
    uuid: str
    name: str
    email: str
   


class TransactionCreate(BaseModel):
    user_id: int
    merchant_raw: str = Field(min_length=1, max_length=200)
    amount: Amount


class TransactionRead(BaseModel):
    id: int
    user_id: int
    merchant_raw: str
    amount: float
    category: Optional[str]
    confidence_score: Optional[float]   # NEW
    date: datetime

    @field_validator("date")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return as_utc(v)  # always serialize with +00:00 so the browser doesn't read it as local time


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int

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
    savings_target_pct: float = Field(ge=0, lt=1)   # user-set, e.g. 0.15 for 15% — REQUIRED, no default baked in
    weekly_income: Optional[Amount] = None   # if omitted, derived from user.monthly_income / 4.33
    category_weights: Optional[dict[Annotated[str, Field(max_length=50)], Annotated[float, Field(ge=0, le=100)]]] = Field(default=None, max_length=20)   # optional override of default priorities


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
    age_score: QuizScore
    income_stability: QuizScore
    investment_horizon: QuizScore
    loss_reaction: QuizScore
    existing_savings_months: QuizScore


class WatchlistCreate(BaseModel):
    user_id: int
    symbol: str = Field(pattern=r"^[0-9A-Za-z]{1,20}$")   # mfapi.in scheme code, e.g. "119551"
    note: Optional[str] = Field(default=None, max_length=200)


class WatchlistRead(BaseModel):
    id: int
    user_id: int
    symbol: str
    note: Optional[str]

class IncomeSourceCreate(BaseModel):
    user_id: int
    label: str = Field(min_length=1, max_length=100)
    amount: Amount
    frequency: Literal["weekly", "monthly", "one_time"]


class IncomeSourceRead(BaseModel):
    id: int
    user_id: int
    label: str
    amount: float
    frequency: str


class TotalIncomeRead(BaseModel):
    recurring_weekly_income: float
    one_time_total: float
    weekly_income: float  # recurring + one_time, for backward compatibility with optimizer calls
    sources: list[IncomeSourceRead]
class UserSync(BaseModel):
    supabase_uid: str = Field(max_length=64)
    email: str = Field(max_length=320)   # ignored: the verified token's email is used
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)

class ExplainContributor(BaseModel):
    feature: str
    contribution: float
    is_amount: bool


class ExplainResponse(BaseModel):
    category: Optional[str]
    confidence: Optional[float]
    method: str
    contributors: list[ExplainContributor]
    note: Optional[str] = None

class PeerRecommendation(BaseModel):
    available: bool
    category: Optional[str] = None
    avg_cut_pct: Optional[float] = None
    peer_count: Optional[int] = None
    similarity_confidence: Optional[float] = None
    note: Optional[str] = None

