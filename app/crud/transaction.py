from sqlalchemy.orm import Session
from app.database.models import Transaction, Wallet, WalletStatus
from app.schemas.transaction import TransactionCreate
from fastapi import HTTPException
import time

def create_transfer_vulnerable(db: Session, transaction: TransactionCreate):
    """
    VULNERABLE IMPLEMENTATION:
    - No locking (FOR UPDATE)
    - Race conditions possible between read and write
    - No atomic transaction block explicitly enforcing isolation
    """
    
    # 1. READ SENDER
    sender = db.query(Wallet).filter(Wallet.id == transaction.from_wallet_id).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender wallet not found")
        
    # 2. READ RECEIVER
    receiver = db.query(Wallet).filter(Wallet.id == transaction.to_wallet_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver wallet not found")

    # 3. VALIDATE
    if sender.balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    if sender.status != WalletStatus.ACTIVE:
         raise HTTPException(status_code=400, detail="Sender wallet inactive")

    # --- RACE CONDITION WINDOW START ---
    # In a real high-concurrency scenario, another thread could debit the sender here
    # leading to a double spend because we used the 'sender.balance' read from Step 1.
    
    # Simulating a tiny delay to make race conditions easier to reproduce in testing
    # time.sleep(0.01) 
    # --- RACE CONDITION WINDOW END ---

    # 4. UPDATE BALANCES (In memory -> DB)
    sender.balance -= transaction.amount
    receiver.balance += transaction.amount
    
    # 5. CREATE TRANSACTION RECORD
    db_txn = Transaction(
        from_wallet_id=transaction.from_wallet_id,
        to_wallet_id=transaction.to_wallet_id,
        amount=transaction.amount
    )
    db.add(db_txn)
    
    # 6. COMMIT
    db.commit()
    db.refresh(db_txn)
    
    return db_txn
