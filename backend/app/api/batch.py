from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database.db import get_db
from app.schemas import batch as batch_schema
from app.schemas import transaction as transaction_schema
from app.crud import batch as batch_crud
from app.crud import transaction as transaction_crud
from app.crud import user as user_crud
from app.crud import wallet as wallet_crud
from app.core import security
from app.schemas import user as user_schema
from app.database.models import BatchStatus, BatchRowStatus
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
    
    # Allow execution if PENDING or if we are resuming (PROCESSING)
    if batch.status not in [BatchStatus.PENDING, BatchStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail=f"Batch cannot be executed in current status: {batch.status}")

    # 2. Parse CSV & Create/Sync Rows
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    rows = list(csv_reader)
    
    # Sync database BatchRow records if they don't exist (first time)
    if not batch.rows:
        for index, row in enumerate(rows):
            batch_crud.create_batch_row(
                db, 
                batch_id=batch_id, 
                index=index, 
                recipient_id=int(row['recipient_id']), 
                amount=float(row['amount'])
            )
        db.refresh(batch)

    # 3. OPTIONAL PRE-CHECK (Non-binding)
    total_batch_amount = sum(float(row['amount']) for row in rows)
    source_wallet = wallet_crud.get_wallet(db, batch.source_wallet_id)
    pre_check_warning = None
    if source_wallet.balance < total_batch_amount:
        pre_check_warning = f"Warning: Source wallet has {source_wallet.balance}, but batch requires {total_batch_amount}. Execution will proceed but may fail mid-way."

    # 4. Update Status to PROCESSING
    if batch.status == BatchStatus.PENDING:
        batch_crud.update_batch_progress(db, batch_id, status=BatchStatus.PROCESSING)

    # 5. Process Rows starting from last_processed_index + 1
    # This provides RESUMABILITY if the server crashed previously
    start_index = batch.last_processed_index + 1
    
    for index in range(start_index, len(rows)):
        row_data = rows[index]
        db_row = batch.rows[index] # Assumes rows are fetched in index order
        
        try:
            recipient_id = int(row_data['recipient_id'])
            amount = float(row_data['amount'])
            
            # Idempotency Key: batch_{id}_row_{index}
            # Reuse logic to ensure retries are safe
            idempotency_key = f"batch_{batch_id}_row_{index}"
            
            tx_data = transaction_schema.TransactionCreate(
                from_wallet_id=batch.source_wallet_id,
                to_wallet_id=recipient_id,
                amount=amount,
                idempotency_key=idempotency_key,
                batch_id=batch_id
            )
            
            # Core transfer logic (Hardened)
            tx = transaction_crud.create_transfer_secure(db, tx_data)
            
            # Update row tracking
            batch_crud.update_batch_row(db, db_row.id, status=BatchRowStatus.SUCCESS, transaction_id=tx.id)
            # Update batch progress
            batch_crud.update_batch_progress(db, batch_id, success=True, amount=amount, is_item=True, last_index=index)
            
        except Exception as e:
            # Individual row failure: Track error but don't stop the whole batch
            batch_crud.update_batch_row(db, db_row.id, status=BatchRowStatus.FAILED, error_message=str(e))
            batch_crud.update_batch_progress(db, batch_id, success=False, is_item=True, last_index=index)

    # 6. Final Status Transition
    final_status = BatchStatus.COMPLETED if batch.failure_count == 0 else BatchStatus.PARTIALLY_FAILED
    batch_crud.update_batch_progress(db, batch_id, status=final_status)
    
    return {
        "status": f"Batch processing finished with state: {final_status}", 
        "batch_id": batch_id,
        "pre_check_warning": pre_check_warning,
        "summary": {
            "total": len(rows),
            "success": batch.success_count,
            "failed": batch.failure_count
        }
    }

@router.post("/{batch_id}/compensate")
def compensate_batch(
    batch_id: int,
    request: batch_schema.BatchCompensationRequest,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    """
    COMPENSATION (Not Rollback):
    Generates reversal transfers for selected successful rows in a batch.
    """
    batch = batch_crud.get_batch(db, batch_id=batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    user = user_crud.get_user_by_username(db, username=current_user.username)
    if batch.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    results = []
    db_rows = batch_crud.get_batch_rows(db, batch_id)
    
    for idx in request.row_indices:
        if idx < 0 or idx >= len(db_rows):
            results.append({"index": idx, "status": "Error", "detail": "Invalid index"})
            continue
            
        row = db_rows[idx]
        if row.status != BatchRowStatus.SUCCESS or not row.transaction_id:
            results.append({"index": idx, "status": "Skipped", "detail": "Row was not successful"})
            continue

        try:
            # Create a REVERSAL transfer
            # From: Original Recipient -> To: Original Source
            rev_tx_data = transaction_schema.TransactionCreate(
                from_wallet_id=row.recipient_id,
                to_wallet_id=batch.source_wallet_id,
                amount=row.amount,
                idempotency_key=f"reversal_batch_{batch_id}_row_{idx}"
            )
            transaction_crud.create_transfer_secure(db, rev_tx_data)
            results.append({"index": idx, "status": "Compensated"})
        except Exception as e:
            results.append({"index": idx, "status": "Failed", "detail": str(e)})

    return {"batch_id": batch_id, "compensation_results": results}
