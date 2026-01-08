from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .db import Base

class WalletStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class BatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"

class BatchRowStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    transaction_pin_hash = Column(String, nullable=True)
    
    wallet = relationship("Wallet", back_populates="owner", uselist=False)
    
    @property
    def has_pin(self) -> bool:
        return self.transaction_pin_hash is not None

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

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    source_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    item_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    last_processed_index = Column(Integer, default=-1)

    transactions = relationship("Transaction", back_populates="batch")
    rows = relationship("BatchRow", back_populates="batch")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    to_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)

    batch = relationship("Batch", back_populates="transactions")
    batch_row = relationship("BatchRow", back_populates="transaction", uselist=False)

class BatchRow(Base):
    __tablename__ = "batch_rows"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    row_index = Column(Integer)
    recipient_id = Column(Integer)
    amount = Column(Float)
    status = Column(Enum(BatchRowStatus), default=BatchRowStatus.SKIPPED)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    error_message = Column(String, nullable=True)

    batch = relationship("Batch", back_populates="rows")
    transaction = relationship("Transaction", back_populates="batch_row")
