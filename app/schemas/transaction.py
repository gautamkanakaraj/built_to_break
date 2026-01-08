from pydantic import BaseModel
from datetime import datetime

class TransactionBase(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float

class TransactionCreate(TransactionBase):
    idempotency_key: str

class Transaction(TransactionBase):
    id: int
    idempotency_key: str
    timestamp: datetime

    class Config:
        from_attributes = True
