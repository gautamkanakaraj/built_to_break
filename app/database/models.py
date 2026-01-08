from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .db import Base

class WalletStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    
    wallet = relationship("Wallet", back_populates="owner", uselist=False)

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)
    status = Column(Enum(WalletStatus), default=WalletStatus.ACTIVE)

    __table_args__ = (
        CheckConstraint('balance >= 0', name='check_min_balance'),
    )

    owner = relationship("User", back_populates="wallet")
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.from_wallet_id")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.to_wallet_id")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    to_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
