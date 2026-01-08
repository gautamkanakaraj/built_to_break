from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .transaction import Transaction
from app.database.models import BatchStatus

class BatchBase(BaseModel):
    source_wallet_id: int

class BatchCreate(BatchBase):
    pass

class BatchItem(BaseModel):
    recipient_id: int
    amount: float

class BatchExecute(BaseModel):
    items: List[BatchItem]

class Batch(BatchBase):
    id: int
    user_id: int
    status: BatchStatus
    total_amount: float
    item_count: int
    success_count: int
    failure_count: int
    timestamp: datetime
    
    # We might not want to return all transactions in a single list for performance
    # but for simplicity in this demo we'll include them.
    transactions: List[Transaction] = []

    class Config:
        from_attributes = True
