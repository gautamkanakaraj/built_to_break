from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import transaction as transaction_schema
from app.crud import transaction as transaction_crud

router = APIRouter()

@router.post("/", response_model=transaction_schema.Transaction)
def transfer_money(transaction: transaction_schema.TransactionCreate, db: Session = Depends(get_db)):
    return transaction_crud.create_transfer_vulnerable(db=db, transaction=transaction)
