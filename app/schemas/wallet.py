from pydantic import BaseModel
from typing import Optional
from app.database.models import WalletStatus

class WalletBase(BaseModel):
    pass

class WalletCreate(WalletBase):
    user_id: int

class Wallet(WalletBase):
    id: int
    user_id: int
    balance: float
    status: WalletStatus

    class Config:
        from_attributes = True

class WalletDeposit(BaseModel):
    amount: float
