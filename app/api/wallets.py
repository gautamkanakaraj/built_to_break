from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import wallet as wallet_schema
from app.crud import wallet as wallet_crud

router = APIRouter()

@router.post("/", response_model=wallet_schema.Wallet)
def create_wallet(wallet: wallet_schema.WalletCreate, db: Session = Depends(get_db)):
    return wallet_crud.create_wallet(db=db, wallet=wallet)

@router.get("/{wallet_id}", response_model=wallet_schema.Wallet)
def read_wallet(wallet_id: int, db: Session = Depends(get_db)):
    db_wallet = wallet_crud.get_wallet(db, wallet_id=wallet_id)
    if db_wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return db_wallet

@router.post("/{wallet_id}/deposit", response_model=wallet_schema.Wallet)
def deposit(wallet_id: int, deposit: wallet_schema.WalletDeposit, db: Session = Depends(get_db)):
    updated_wallet = wallet_crud.deposit_wallet(db, wallet_id=wallet_id, amount=deposit.amount)
    if not updated_wallet:
         raise HTTPException(status_code=404, detail="Wallet not found")
    return updated_wallet
@router.post("/balances", response_model=List[wallet_schema.Wallet])
def read_wallets_balances(wallet_ids: List[int], db: Session = Depends(get_db)):
    return wallet_crud.get_wallets_balances(db, wallet_ids=wallet_ids)
