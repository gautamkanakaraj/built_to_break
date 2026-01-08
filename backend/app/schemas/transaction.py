from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransactionBase(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float

class TransactionCreate(TransactionBase):
    idempotency_key: str
    pin: str
    batch_id: Optional[int] = None

class Transaction(TransactionBase):
    id: int
    idempotency_key: str
    timestamp: datetime
    batch_id: Optional[int] = None

    class Config:
        from_attributes = True
