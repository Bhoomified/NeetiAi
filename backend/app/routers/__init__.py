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

router = APIRouter()


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

    weekly_income = payload.weekly_income or (user.monthly_income / 4.33)

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
    # Pull real backend data relevant to likely intents — e.g. this week's forecast —
    # so template responses use ACTUAL numbers, never invented ones
    user_transactions = session.exec(select(Transaction).where(Transaction.user_id == payload.user_id)).all()

    backend_data = None
    if user_transactions:
        recent_amount = sum(t.amount for t in user_transactions[-5:])  # simple recent-spend context for now
        recent_category = user_transactions[-1].category
        backend_data = {"amount": recent_amount, "category": recent_category}

    result = chatbot_chat(payload.message, backend_data=backend_data)

    log = ChatLog(user_id=payload.user_id, role="user", message=payload.message)
    session.add(log)
    log2 = ChatLog(user_id=payload.user_id, role="assistant", message=result["response"])
    session.add(log2)
    session.commit()

    return result
