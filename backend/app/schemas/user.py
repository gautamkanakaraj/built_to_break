from pydantic import BaseModel
from typing import Optional
from .wallet import Wallet

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    wallet: Optional[Wallet] = None
    has_pin: bool = False
    
    class Config:
        from_attributes = True

class UserSetPin(BaseModel):
    pin: str

class Token(BaseModel):
    access_token: str
    token_type: str
