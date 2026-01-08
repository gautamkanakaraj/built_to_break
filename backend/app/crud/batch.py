from sqlalchemy.orm import Session
from app.database.models import Batch, BatchStatus, Transaction, BatchRow, BatchRowStatus
from app.schemas.batch import BatchCreate
from datetime import datetime
from typing import Optional, List

def create_batch(db: Session, batch: BatchCreate, user_id: int):
    # Check batch-level idempotency
    if batch.idempotency_key:
        existing = get_batch_by_idempotency_key(db, batch.idempotency_key)
        if existing:
            return existing

    db_batch = Batch(
        user_id=user_id,
        source_wallet_id=batch.source_wallet_id,
        idempotency_key=batch.idempotency_key,
        status=BatchStatus.PENDING
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_batch_by_idempotency_key(db: Session, key: str):
    return db.query(Batch).filter(Batch.idempotency_key == key).first()

def get_batch(db: Session, batch_id: int):
    return db.query(Batch).filter(Batch.id == batch_id).first()

def get_batches_by_user(db: Session, user_id: int):
    return db.query(Batch).filter(Batch.user_id == user_id).order_by(Batch.timestamp.desc()).all()

def update_batch_progress(db: Session, batch_id: int, status: BatchStatus = None, success: bool = True, amount: float = 0.0, is_item: bool = False, last_index: int = None):
    db_batch = get_batch(db, batch_id)
    if not db_batch:
        return None
    
    if status:
        db_batch.status = status
    
    if last_index is not None:
        db_batch.last_processed_index = last_index
    
    if is_item:
        db_batch.item_count += 1
        if success:
            db_batch.success_count += 1
            db_batch.total_amount += amount
        else:
            db_batch.failure_count += 1
        
    db.commit()
    db.refresh(db_batch)
    return db_batch

def create_batch_row(db: Session, batch_id: int, index: int, recipient_id: int, amount: float):
    db_row = BatchRow(
        batch_id=batch_id,
        row_index=index,
        recipient_id=recipient_id,
        amount=amount,
        status=BatchRowStatus.SKIPPED
    )
    db.add(db_row)
    db.commit()
    db.refresh(db_row)
    return db_row

def update_batch_row(db: Session, row_id: int, status: BatchRowStatus, transaction_id: Optional[int] = None, error_message: Optional[str] = None):
    db_row = db.query(BatchRow).filter(BatchRow.id == row_id).first()
    if db_row:
        db_row.status = status
        db_row.transaction_id = transaction_id
        db_row.error_message = error_message
        db.commit()
        db.refresh(db_row)
    return db_row

def get_batch_rows(db: Session, batch_id: int) -> List[BatchRow]:
    return db.query(BatchRow).filter(BatchRow.batch_id == batch_id).order_by(BatchRow.row_index).all()
