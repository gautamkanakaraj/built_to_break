from sqlalchemy.orm import Session
from app.database.models import Batch, BatchStatus, Transaction
from app.schemas.batch import BatchCreate
from datetime import datetime

def create_batch(db: Session, batch: BatchCreate, user_id: int):
    db_batch = Batch(
        user_id=user_id,
        source_wallet_id=batch.source_wallet_id,
        status=BatchStatus.PENDING
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_batch(db: Session, batch_id: int):
    return db.query(Batch).filter(Batch.id == batch_id).first()

def get_batches_by_user(db: Session, user_id: int):
    return db.query(Batch).filter(Batch.user_id == user_id).order_by(Batch.timestamp.desc()).all()

def update_batch_progress(db: Session, batch_id: int, status: BatchStatus = None, success: bool = True, amount: float = 0.0, is_item: bool = False):
    db_batch = get_batch(db, batch_id)
    if not db_batch:
        return None
    
    if status:
        db_batch.status = status
    
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
