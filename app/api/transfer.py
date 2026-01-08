from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import transaction as transaction_schema
from app.crud import transaction as transaction_crud
from app.core import security
from app.schemas import user as user_schema

router = APIRouter()

@router.post("/", response_model=transaction_schema.Transaction)
def transfer_money(
    transaction: transaction_schema.TransactionCreate, 
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    """
    Secure Transfer Endpoint:
    - Requires Authentication (JWT)
    - Uses 'create_transfer_secure' for Acid compliance, Locking, and Idempotency
    """
    return transaction_crud.create_transfer_secure(db=db, transaction=transaction)
