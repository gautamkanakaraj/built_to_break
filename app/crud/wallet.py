from sqlalchemy.orm import Session
from app.database.models import Wallet
from app.schemas.wallet import WalletCreate

def create_wallet(db: Session, wallet: WalletCreate):
    db_wallet = Wallet(user_id=wallet.user_id)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet

def get_wallet(db: Session, wallet_id: int):
    return db.query(Wallet).filter(Wallet.id == wallet_id).first()

def deposit_wallet(db: Session, wallet_id: int, amount: float):
    wallet = get_wallet(db, wallet_id)
    if wallet:
        wallet.balance += amount
        db.commit()
        db.refresh(wallet)
    return wallet
