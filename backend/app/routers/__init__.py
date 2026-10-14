from datetime import timedelta
from typing import Annotated

from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Query, Request # type: ignore
from sqlmodel import Session, select # type: ignore
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.database import get_session
from app.auth import current_user, ensure_owner, token_claims
from app.rate_limit import limiter, CHAT_LIMIT, SEARCH_LIMIT
from app.models import User, Transaction, utcnow
from app.schemas import UserRead, TransactionCreate, TransactionRead, TransactionPage
from app.ml_categorizer import categorize_transaction
from app.ml_forecast import forecast_user
from app.ml_optimizer import optimize_budget
from app.schemas import ForecastRead, BudgetOptimizeRequest, BudgetOptimizeResponse
from app.ml_chatbot import chat as chatbot_chat
from app.models import ChatLog
from app.ml_investments import classify_risk_profile, fetch_fund_nav_history, detect_opportunity, search_funds
from app.models import InvestmentWatchlist
from app.schemas import RiskQuizRequest, WatchlistCreate, WatchlistRead
from app.models import IncomeSource
from app.schemas import IncomeSourceCreate, IncomeSourceRead, TotalIncomeRead
from app.schemas import UserSync
from app.ml_explain import explain_categorization
from app.schemas import ExplainResponse
from app.ml_recommend import get_peer_recommendation
from app.schemas import PeerRecommendation

router = APIRouter()


def compute_income_breakdown(user_id: int, session: Session) -> dict:
    """Returns recurring weekly income and one-time income separately."""
    sources = session.exec(select(IncomeSource).where(IncomeSource.user_id == user_id)).all()
    recurring_weekly = 0.0
    one_time_total = 0.0
    for s in sources:
        if s.frequency == "weekly":
            recurring_weekly += s.amount
        elif s.frequency == "monthly":
            recurring_weekly += s.amount / 4.33
        elif s.frequency == "one_time":
            one_time_total += s.amount
    return {
        "recurring_weekly_income": recurring_weekly,
        "one_time_total": one_time_total,
        "weekly_income": recurring_weekly + one_time_total,
    }


# The forecaster's features are the last 4 weekly totals plus per-category shares;
# half a year of history covers both without loading a user's whole ledger.
FORECAST_WINDOW_WEEKS = 26


def load_forecast_rows(user_id: int, session: Session) -> list:
    """Only the three columns forecast_user reads, for the recent window."""
    since = utcnow() - timedelta(weeks=FORECAST_WINDOW_WEEKS)
    return session.exec(
        select(Transaction.date, Transaction.amount, Transaction.category)
        .where(Transaction.user_id == user_id, Transaction.date >= since)
    ).all()


def compute_weekly_income(user_id: int, session: Session) -> float:
    """Kept for backward compatibility — used by /budget/optimize and /chat."""
    return compute_income_breakdown(user_id, session)["weekly_income"]

@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, me: User = Depends(current_user)):
    ensure_owner(user_id, me)
    return me


@router.post("/transactions", response_model=TransactionRead)
def create_transaction(tx: TransactionCreate, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(tx.user_id, me)
    category, confidence = categorize_transaction(tx.merchant_raw, tx.amount)
    db_tx = Transaction(
        user_id=tx.user_id,
        merchant_raw=tx.merchant_raw,
        amount=tx.amount,
        category=category,
        confidence_score=confidence,
    )
    session.add(db_tx)
    session.commit()
    session.refresh(db_tx)
    return db_tx


@router.get("/transactions/{user_id}", response_model=TransactionPage)
def get_transactions(
    user_id: int,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_session),
    me: User = Depends(current_user),
):
    """Newest first, one page at a time (served by the (user_id, date) index)."""
    ensure_owner(user_id, me)
    total = session.exec(select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)).one()
    items = session.exec(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get("/transactions/{transaction_id}/explain", response_model=ExplainResponse)
def explain_transaction(transaction_id: int, session: Session = Depends(get_session), me: User = Depends(current_user)):
    tx = session.get(Transaction, transaction_id)
    if not tx or tx.user_id != me.id:  # 404, not 403: don't reveal that another user's row exists
        raise HTTPException(status_code=404, detail="Transaction not found")
    return explain_categorization(tx.merchant_raw, tx.amount)

@router.get("/forecast/{user_id}", response_model=ForecastRead)
def get_forecast(user_id: int, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(user_id, me)

    result = forecast_user(load_forecast_rows(user_id, session))
    return {"user_id": user_id, **result}


@router.post("/budget/optimize", response_model=BudgetOptimizeResponse)
def budget_optimize(payload: BudgetOptimizeRequest, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(payload.user_id, me)

    forecast = forecast_user(load_forecast_rows(payload.user_id, session))

    predicted_spend = {c["category"]: c["predicted_amount"] for c in forecast["categories"]}
    if not predicted_spend:
        raise HTTPException(status_code=400, detail="Not enough transaction history to build a budget yet.")

    weekly_income = payload.weekly_income or compute_weekly_income(payload.user_id, session)

    result, error = optimize_budget(
        predicted_category_spend=predicted_spend,
        weekly_income=weekly_income,
        savings_target_pct=payload.savings_target_pct,
        category_weights=payload.category_weights,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


class ChatRequest(BaseModel):
    user_id: int
    message: str = Field(min_length=1, max_length=1000)


@router.post("/chat")
@limiter.limit(CHAT_LIMIT)
def chat_endpoint(request: Request, payload: ChatRequest, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(payload.user_id, me)

    user_transactions = session.exec(select(Transaction).where(Transaction.user_id == payload.user_id)).all()
    income = compute_income_breakdown(payload.user_id, session)

    def forecast_fn():
        return forecast_user(user_transactions) if user_transactions else None

    def optimize_fn():
        forecast = forecast_fn()
        predicted_spend = {c["category"]: c["predicted_amount"] for c in (forecast or {}).get("categories", [])}
        if not predicted_spend or not income["weekly_income"]:
            return None
        result, _ = optimize_budget(predicted_spend, income["weekly_income"], savings_target_pct=0.15)
        return result

    result = chatbot_chat(payload.message, user_transactions, income, forecast_fn, optimize_fn)

    session.add(ChatLog(user_id=payload.user_id, role="user", message=payload.message))
    session.add(ChatLog(user_id=payload.user_id, role="assistant", message=result["response"]))
    session.commit()

    return result


@router.post("/investments/risk-profile")
def risk_profile(payload: RiskQuizRequest, claims: dict = Depends(token_claims)):
    profile = classify_risk_profile(
        payload.age_score, payload.income_stability, payload.investment_horizon,
        payload.loss_reaction, payload.existing_savings_months,
    )
    return {"risk_profile": profile}


@router.post("/investments/watchlist", response_model=WatchlistRead)
def add_to_watchlist(payload: WatchlistCreate, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(payload.user_id, me)
    existing = session.exec(
        select(InvestmentWatchlist).where(
            InvestmentWatchlist.user_id == payload.user_id,
            InvestmentWatchlist.symbol == payload.symbol,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This fund is already on your watchlist.")

    entry = InvestmentWatchlist(user_id=payload.user_id, symbol=payload.symbol, note=payload.note)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/investments/opportunities/{user_id}")
async def check_opportunities(user_id: int, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(user_id, me)
    watchlist = session.exec(select(InvestmentWatchlist).where(InvestmentWatchlist.user_id == user_id)).all()
    if not watchlist:
        return {"opportunities": [], "note": "No funds on your watchlist yet."}

    results = []
    for entry in watchlist:
        try:
            nav_history, meta = await fetch_fund_nav_history(entry.symbol)
            signal = detect_opportunity(nav_history)
            results.append({
                "symbol": entry.symbol,
                "fund_name": meta.get("scheme_name", "Unknown"),
                "signal": signal,
            })
        except Exception as e:
            results.append({"symbol": entry.symbol, "error": f"Could not fetch data: {e}"})

    return {"opportunities": results}


@router.get("/investments/search")
@limiter.limit(SEARCH_LIMIT)
async def search_investments(request: Request, q: Annotated[str, Query(max_length=100)], claims: dict = Depends(token_claims)):
    if len(q) < 2:
        return []
    results = await search_funds(q)
    return results[:10]


@router.post("/income-sources", response_model=IncomeSourceRead)
def add_income_source(payload: IncomeSourceCreate, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(payload.user_id, me)
    source = IncomeSource(**payload.model_dump())
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.get("/income-sources/{user_id}", response_model=TotalIncomeRead)
def get_income_sources(user_id: int, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(user_id, me)
    sources = session.exec(select(IncomeSource).where(IncomeSource.user_id == user_id)).all()
    breakdown = compute_income_breakdown(user_id, session)
    return {
        "recurring_weekly_income": round(breakdown["recurring_weekly_income"], 2),
        "one_time_total": round(breakdown["one_time_total"], 2),
        "weekly_income": round(breakdown["weekly_income"], 2),
        "sources": sources,
    }


@router.delete("/income-sources/{source_id}")
def delete_income_source(source_id: int, session: Session = Depends(get_session), me: User = Depends(current_user)):
    source = session.get(IncomeSource, source_id)
    if not source or source.user_id != me.id:  # 404, not 403: don't reveal that another user's row exists
        raise HTTPException(404, "Income source not found")
    session.delete(source)
    session.commit()
    return {"deleted": True}


@router.post("/users/sync", response_model=UserRead)
def sync_user(payload: UserSync, session: Session = Depends(get_session), claims: dict = Depends(token_claims)):
    """Called right after login/signup — finds, links or creates the matching backend user.

    Identity (uid, email) comes from the verified token; the body only supplies names.
    Idempotent and race-safe: the browser fires this from both getSession and
    onAuthStateChange, so two requests can arrive together. The loser of the
    insert race hits the unique constraint, rolls back and re-reads the winner's row.
    """
    uid = claims["sub"]
    email = claims.get("email") or ""
    if payload.supabase_uid != uid:
        raise HTTPException(status_code=403, detail="Token does not match the account being synced.")
    if not email:
        raise HTTPException(status_code=400, detail="Your login has no email address.")

    for _ in range(2):
        existing = session.exec(select(User).where(User.supabase_uid == uid)).first()
        if existing:
            return existing

        # Same email under another Supabase uid (e.g. signed up by email, later via Google):
        # link the existing row instead of violating the unique email constraint — but only
        # once the provider has verified the email, or anyone could claim the account.
        user = session.exec(select(User).where(func.lower(User.email) == email.lower())).first()
        if user:
            if not (claims.get("user_metadata") or {}).get("email_verified"):
                raise HTTPException(status_code=409, detail="An account with this email already exists. Verify your email to link it.")
            user.supabase_uid = uid
        else:
            user = User(
                supabase_uid=uid,
                name=f"{payload.first_name} {payload.last_name}".strip(),
                email=email,
            )
        session.add(user)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            continue
        session.refresh(user)
        return user

    raise HTTPException(status_code=409, detail="Could not sync your account, please retry.")

@router.get("/recommendations/{user_id}", response_model=PeerRecommendation)
def get_recommendation(user_id: int, session: Session = Depends(get_session), me: User = Depends(current_user)):
    ensure_owner(user_id, me)

    transactions = session.exec(select(Transaction).where(Transaction.user_id == user_id)).all()
    category_spend = {}
    for t in transactions:
        if t.category:
            category_spend[t.category] = category_spend.get(t.category, 0.0) + t.amount

    return get_peer_recommendation(category_spend)