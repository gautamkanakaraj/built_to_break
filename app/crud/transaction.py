from sqlalchemy.orm import Session
from app.database.models import Transaction, Wallet, WalletStatus
from app.schemas.transaction import TransactionCreate
from fastapi import HTTPException
from sqlalchemy import or_

def create_transfer_secure(db: Session, transaction: TransactionCreate):
    """
    SECURE IMPLEMENTATION:
    - Atomicity: Wrapped in a single DB transaction scope (via session)
    - Concurrency: Uses SELECT ... FOR UPDATE (row locking)
    - Idempotency: Checks for existence of idempotency_key
    - Consistency: Enforces ordering to prevent deadlocks
    """
    
    # 1. IDEMPOTENCY CHECK
    # Check if a transaction with this key already exists
    existing_txn = db.query(Transaction).filter(
        Transaction.idempotency_key == transaction.idempotency_key
    ).first()
    
    if existing_txn:
        # Return the existing transaction (Idempotent response)
        # In a real system, we might verify that the parameters match
        return existing_txn

    # 2. LOCKING & ORDERING
    # Prevent Deadlocks: Always lock in consistent order (Low ID first)
    first_id = min(transaction.from_wallet_id, transaction.to_wallet_id)
    second_id = max(transaction.from_wallet_id, transaction.to_wallet_id)
    
    # Lock rows
    # populate_existing() ensures we refresh correctly
    # with_for_update() adds "FOR UPDATE" clause
    try:
        w1 = db.query(Wallet).filter(Wallet.id == first_id).with_for_update().first()
        w2 = db.query(Wallet).filter(Wallet.id == second_id).with_for_update().first()
    except Exception as e:
        db.rollback()
        raise e

    if not w1 or not w2:
        db.rollback()
        raise HTTPException(status_code=404, detail="One or more wallets not found")

    # Map back to sender/receiver
    sender = w1 if w1.id == transaction.from_wallet_id else w2
    receiver = w1 if w1.id == transaction.to_wallet_id else w2

    # 3. VALIDATION (Invariant Check)
    if sender.balance < transaction.amount:
        db.rollback()
        raise HTTPException(status_code=400, detail="Insufficient funds")

    if sender.status != WalletStatus.ACTIVE:
        db.rollback()
        raise HTTPException(status_code=400, detail="Sender wallet inactive")

    # 4. EXECUTE TRANSFER (Atomic Update)
    sender.balance -= transaction.amount
    receiver.balance += transaction.amount
    
    # 5. CREATE RECORD
    db_txn = Transaction(
        from_wallet_id=transaction.from_wallet_id,
        to_wallet_id=transaction.to_wallet_id,
        amount=transaction.amount,
        idempotency_key=transaction.idempotency_key,
        batch_id=transaction.batch_id
    )
    db.add(db_txn)
    
    # 6. COMMIT
    # If any error happens before this, DB rolls back automatically or we caught it.
    try:
        db.commit()
        db.refresh(db_txn)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Transaction failed: {str(e)}")
        
    return db_txn

# Keep vulnerable version for reference or legacy compatibility if needed, 
# but API should call secure version.
def create_transfer_vulnerable(db: Session, transaction: TransactionCreate):
    # ... legacy code ...
    pass 

def get_transactions_by_wallet(db: Session, wallet_id: int):
    return db.query(Transaction).filter(
        or_(
            Transaction.from_wallet_id == wallet_id,
            Transaction.to_wallet_id == wallet_id
        )
    ).order_by(Transaction.timestamp.desc()).all()
