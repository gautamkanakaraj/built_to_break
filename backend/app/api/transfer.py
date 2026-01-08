from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import transaction as transaction_schema
from app.crud import transaction as transaction_crud
from app.core import security
from app.schemas import user as user_schema
from typing import List

router = APIRouter()

@router.post("/", response_model=transaction_schema.Transaction)
def transfer_money(
    transaction: transaction_schema.TransactionCreate, 
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    # 1. Verify that current_user owns from_wallet_id
    from app.crud import user as user_crud
    from app.crud import wallet as wallet_crud
    
    user = user_crud.get_user_by_username(db, username=current_user.username)
    wallet = wallet_crud.get_wallet(db, wallet_id=transaction.from_wallet_id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Source wallet not found")
    
    if wallet.user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not own the source wallet")

    return transaction_crud.create_transfer_secure(db=db, transaction=transaction)

@router.get("/history/{wallet_id}", response_model=List[transaction_schema.Transaction])
def get_history(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    # Verification: Ensure current_user owns the wallet
    from app.crud import wallet as wallet_crud
    wallet = wallet_crud.get_wallet(db, wallet_id=wallet_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    from app.crud import user as user_crud
    user = user_crud.get_user_by_username(db, username=current_user.username)
    if wallet.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this wallet's history")
        
    return transaction_crud.get_transactions_by_wallet(db, wallet_id=wallet_id)
