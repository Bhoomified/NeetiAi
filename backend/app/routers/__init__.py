from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Transaction
from app.schemas import UserCreate, UserRead, TransactionCreate, TransactionRead
from app.ml_categorizer import categorize_transaction

router = APIRouter()


@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(name=user.name, email=user.email)
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