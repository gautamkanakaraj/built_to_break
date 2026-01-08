from sqlalchemy.orm import Session
from app.database.models import User, Wallet
from app.schemas.user import UserCreate

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create associated wallet
    db_wallet = Wallet(user_id=db_user.id, balance=0.0)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
