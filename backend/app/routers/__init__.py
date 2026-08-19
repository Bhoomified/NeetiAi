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
            weekly_income = user.monthly_income / 4.33
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