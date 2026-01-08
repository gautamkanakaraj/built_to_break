from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .transaction import Transaction
from app.database.models import BatchStatus, BatchRowStatus

class BatchBase(BaseModel):
    source_wallet_id: int
    idempotency_key: Optional[str] = None

class BatchCreate(BatchBase):
    pass

class BatchItem(BaseModel):
    recipient_id: int
    amount: float

class BatchExecute(BaseModel):
    items: List[BatchItem]
    pin: str

class BatchRow(BaseModel):
    id: int
    batch_id: int
    row_index: int
    recipient_id: int
    amount: float
    status: BatchRowStatus
    transaction_id: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class Batch(BatchBase):
    id: int
    user_id: int
    status: BatchStatus
    total_amount: float
    item_count: int
    success_count: int
    failure_count: int
    last_processed_index: int
    timestamp: datetime
    rows: List[BatchRow] = []

    class Config:
        from_attributes = True

class BatchCompensationRequest(BaseModel):
    row_indices: List[int]
    pin: str
