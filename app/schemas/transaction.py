from pydantic import BaseModel
from datetime import datetime

class TransactionBase(BaseModel):
    from_wallet_id: int
    to_wallet_id: int
    amount: float

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
