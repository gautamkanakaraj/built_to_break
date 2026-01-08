from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import user as user_schema
from app.crud import user as user_crud
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from app.core import security
from app.database import models

router = APIRouter()

@router.post("/token", response_model=user_schema.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate Token
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=user_schema.User)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    user = user_crud.get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/me/pin")
def set_transaction_pin(
    pin_data: user_schema.UserSetPin,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(security.get_current_user)
):
    user = user_crud.get_user_by_username(db, username=current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        hashed_pin = security.get_pin_hash(pin_data.pin)
        user_crud.update_user_pin(db, user_id=user.id, hashed_pin=hashed_pin)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return {"status": "Transaction PIN set successfully"}

@router.post("/", response_model=user_schema.User)
def create_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    return user_crud.create_user(db=db, user=user)

@router.get("/", response_model=List[user_schema.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = user_crud.get_users(db, skip=skip, limit=limit)
    return users
