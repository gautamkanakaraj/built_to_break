from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database.models import Wallet
from typing import List
from app.schemas.wallet import WalletCreate

def create_wallet(db: Session, wallet: WalletCreate):
    db_wallet = Wallet(user_id=wallet.user_id)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet

def get_wallet(db: Session, wallet_id: int):
    return db.query(Wallet).filter(Wallet.id == wallet_id).first()

def get_wallets_by_user(db: Session, user_id: int):
    return db.query(Wallet).filter(Wallet.user_id == user_id).all()

def deposit_wallet(db: Session, wallet_id: int, amount: float):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive. Use /transfer/ for movements.")
    wallet = get_wallet(db, wallet_id)
    if wallet:
        wallet.balance += amount
        db.commit()
        db.refresh(wallet)
    return wallet
    return wallet

def get_wallets_balances(db: Session, wallet_ids: List[int]):
    """
    Consistent Multi-Wallet Read:
    By default Postgres READ COMMITTED can show skew.
    This function can be extended to use REPEATABLE READ if needed,
    but even a single SELECT ... WHERE id IN (...) in READ COMMITTED
    provides a consistent snapshot relative to a single point in time 
    for all rows matched by the statement.
    """
    return db.query(Wallet).filter(Wallet.id.in_(wallet_ids)).all()
