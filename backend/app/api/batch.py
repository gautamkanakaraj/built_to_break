from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database.db import get_db
from app.schemas import batch as batch_schema
from app.schemas import transaction as transaction_schema
from app.crud import batch as batch_crud
from app.crud import transaction as transaction_crud
from app.crud import user as user_crud
from app.core import security
from app.schemas import user as user_schema
from app.database.models import BatchStatus
import io
import csv

router = APIRouter()

@router.get("/", response_model=List[batch_schema.Batch])
def list_batches(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    user = user_crud.get_user_by_username(db, username=current_user.username)
    return batch_crud.get_batches_by_user(db, user_id=user.id)

@router.get("/{batch_id}", response_model=batch_schema.Batch)
def get_batch_details(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    batch = batch_crud.get_batch(db, batch_id=batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    user = user_crud.get_user_by_username(db, username=current_user.username)
    if batch.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this batch")
        
    return batch

@router.post("/", response_model=batch_schema.Batch)
def create_new_batch(
    batch: batch_schema.BatchCreate,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    user = user_crud.get_user_by_username(db, username=current_user.username)
    return batch_crud.create_batch(db, batch=batch, user_id=user.id)

@router.post("/{batch_id}/execute")
async def execute_batch(
    batch_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    # 1. Verify Batch & Ownership
    batch = batch_crud.get_batch(db, batch_id=batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    user = user_crud.get_user_by_username(db, username=current_user.username)
    if batch.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if batch.status != BatchStatus.PENDING:
        raise HTTPException(status_code=400, detail="Batch already processed or processing")

    # 2. Parse CSV
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    # 3. Update Status to PROCESSING
    batch_crud.update_batch_progress(db, batch_id, status=BatchStatus.PROCESSING)

    # 4. Process Rows
    # Note: For a real high-throughput system, we'd offload this to Celery/Worker
    # For this demo, we'll process synchronously as per requirement
    rows = list(csv_reader)
    for index, row in enumerate(rows):
        try:
            recipient_id = int(row['recipient_id'])
            amount = float(row['amount'])
            
            # Idempotency Key: batch_{id}_row_{index}
            idempotency_key = f"batch_{batch_id}_row_{index}"
            
            tx_data = transaction_schema.TransactionCreate(
                from_wallet_id=batch.source_wallet_id,
                to_wallet_id=recipient_id,
                amount=amount,
                idempotency_key=idempotency_key,
                batch_id=batch_id
            )
            
            transaction_crud.create_transfer_secure(db, tx_data)
            batch_crud.update_batch_progress(db, batch_id, success=True, amount=amount, is_item=True)
            
        except Exception as e:
            # Individual row failure doesn't stop the batch
            print(f"Row {index} failed: {str(e)}")
            batch_crud.update_batch_progress(db, batch_id, success=False, is_item=True)

    # 5. Mark COMPLETED
    batch_crud.update_batch_progress(db, batch_id, status=BatchStatus.COMPLETED)
    
    return {"status": "Batch processing finished", "batch_id": batch_id}
