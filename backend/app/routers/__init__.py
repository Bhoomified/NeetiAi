from pydantic import BaseModel


from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlmodel import Session, select # type: ignore
from app.database import get_session
from app.models import User, Transaction
from app.schemas import UserCreate, UserRead, TransactionCreate, TransactionRead
from app.ml_categorizer import categorize_transaction
from app.ml_forecast import forecast_user
from app.ml_optimizer import optimize_budget
from app.schemas import ForecastRead, BudgetOptimizeRequest, BudgetOptimizeResponse
from app.ml_chatbot import chat as chatbot_chat
from app.models import ChatLog
from app.ml_investments import classify_risk_profile, fetch_fund_nav_history, detect_opportunity,search_funds
from app.models import InvestmentWatchlist
from app.schemas import RiskQuizRequest, WatchlistCreate, WatchlistRead
from app.models import IncomeSource
from app.schemas import IncomeSourceCreate, IncomeSourceRead, TotalIncomeRead

router = APIRouter()

def compute_weekly_income(user_id: int, session: Session) -> float:
    """Base user.monthly_income PLUS all active income sources, normalized to weekly."""
    user = session.get(User, user_id)
    base_weekly = (user.monthly_income if user else 0) / 4.33

    sources = session.exec(select(IncomeSource).where(IncomeSource.user_id == user_id)).all()
    extra_weekly = 0.0
    for s in sources:
        if s.frequency == "weekly":
            extra_weekly += s.amount
        else:  # monthly
            extra_weekly += s.amount / 4.33

    return base_weekly + extra_weekly

@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(name=user.name, email=user.email, monthly_income=user.monthly_income)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/transactions", response_model=TransactionRead)
def create_transaction(tx: TransactionCreate, session: Session = Depends(get_session)):
    category, confidence = categorize_transaction(tx.merchant_raw, tx.amount)
    db_tx = Transaction(
        user_id=tx.user_id,
        merchant_raw=tx.merchant_raw,
        amount=tx.amount,
        category=category,
        confidence_score=confidence,   # NEW
    )
    session.add(db_tx)
    session.commit()
    session.refresh(db_tx)
    return db_tx


@router.get("/transactions/{user_id}", response_model=list[TransactionRead])
def get_transactions(user_id: int, session: Session = Depends(get_session)):
    statement = select(Transaction).where(Transaction.user_id == user_id)
    results = session.exec(statement).all()
    return results

@router.get("/forecast/{user_id}", response_model=ForecastRead)
def get_forecast(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = session.exec(select(Transaction).where(Transaction.user_id == user_id)).all()
    result = forecast_user(transactions)
    return {"user_id": user_id, **result}


@router.post("/budget/optimize", response_model=BudgetOptimizeResponse)
def budget_optimize(payload: BudgetOptimizeRequest, session: Session = Depends(get_session)):
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = session.exec(select(Transaction).where(Transaction.user_id == payload.user_id)).all()
    forecast = forecast_user(transactions)

    predicted_spend = {c["category"]: c["predicted_amount"] for c in forecast["categories"]}
    if not predicted_spend:
        raise HTTPException(status_code=400, detail="Not enough transaction history to build a budget yet.")

    weekly_income = payload.weekly_income or compute_weekly_income(payload.user_id, session)

    result, error = optimize_budget(
        predicted_category_spend=predicted_spend,
        weekly_income=weekly_income,
        savings_target_pct=payload.savings_target_pct,   # <-- from the request, exactly as you wanted
        category_weights=payload.category_weights,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result

class ChatRequest(BaseModel):
    user_id: int
    message: str

@router.post("/chat")
def chat_endpoint(payload: ChatRequest, session: Session = Depends(get_session)):
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_transactions = session.exec(select(Transaction).where(Transaction.user_id == payload.user_id)).all()

    # First pass: classify + extract entities WITHOUT backend data, so we know
    # which intent fired before deciding what real data to fetch
    from app.ml_chatbot import predict_intent, extract_amount, extract_category, extract_timeframe

    intent, confidence = predict_intent(payload.message)
    entities = {
        "amount": extract_amount(payload.message),
        "category": extract_category(payload.message),
        "timeframe": extract_timeframe(payload.message),
    }

    backend_data = None

    if intent == "category_query" and entities["category"]:
        # Real category-specific total, not a generic blob
        cat_total = sum(t.amount for t in user_transactions if t.category == entities["category"])
        backend_data = {"amount": cat_total, "category": entities["category"]}

    elif intent == "spending_complaint" and entities["category"]:
        cat_total = sum(t.amount for t in user_transactions if t.category == entities["category"])
        backend_data = {"amount": cat_total, "category": entities["category"]}

    elif intent == "savings_flex":
        # Pull the REAL projected savings from your optimizer, not last-5-transactions
        forecast = forecast_user(user_transactions)
        predicted_spend = {c["category"]: c["predicted_amount"] for c in forecast["categories"]}
        if predicted_spend:
            weekly_income = compute_weekly_income(payload.user_id, session)
            opt_result, _ = optimize_budget(predicted_spend, weekly_income, savings_target_pct=0.15)
            if opt_result:
                backend_data = {"amount": opt_result["projected_savings"]}

    elif intent == "budget_help" and entities["category"]:
        forecast = forecast_user(user_transactions)
        cat_forecast = next((c for c in forecast["categories"] if c["category"] == entities["category"]), None)
        if cat_forecast:
            backend_data = {"amount": cat_forecast["predicted_amount"] * 0.8, "category": entities["category"]}

    result = chatbot_chat(payload.message, backend_data=backend_data)

    session.add(ChatLog(user_id=payload.user_id, role="user", message=payload.message))
    session.add(ChatLog(user_id=payload.user_id, role="assistant", message=result["response"]))
    session.commit()

    return result

@router.post("/investments/risk-profile")
def risk_profile(payload: RiskQuizRequest):
    profile = classify_risk_profile(
        payload.age_score, payload.income_stability, payload.investment_horizon,
        payload.loss_reaction, payload.existing_savings_months,
    )
    return {"risk_profile": profile}

@router.post("/investments/watchlist", response_model=WatchlistRead)
def add_to_watchlist(payload: WatchlistCreate, session: Session = Depends(get_session)):
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
async def check_opportunities(user_id: int, session: Session = Depends(get_session)):
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
async def search_investments(q: str):
    if len(q) < 2:
        return []
    results = await search_funds(q)
    return results[:10]  

@router.post("/income-sources", response_model=IncomeSourceRead)
def add_income_source(payload: IncomeSourceCreate, session: Session = Depends(get_session)):
    if payload.frequency not in ("monthly", "weekly"):
        raise HTTPException(400, "frequency must be 'monthly' or 'weekly'")
    source = IncomeSource(**payload.model_dump())
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.get("/income-sources/{user_id}", response_model=TotalIncomeRead)
def get_income_sources(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    sources = session.exec(select(IncomeSource).where(IncomeSource.user_id == user_id)).all()
    return {
        "weekly_income": round(compute_weekly_income(user_id, session), 2),
        "monthly_income": user.monthly_income,
        "sources": sources,
    }


@router.delete("/income-sources/{source_id}")
def delete_income_source(source_id: int, session: Session = Depends(get_session)):
    source = session.get(IncomeSource, source_id)
    if not source:
        raise HTTPException(404, "Income source not found")
    session.delete(source)
    session.commit()
    return {"deleted": True}