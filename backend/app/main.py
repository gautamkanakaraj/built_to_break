from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import models, db
from app.api import users, wallets, transfer, batch

# Create tables
models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(title="G-Wallet Backend (Decoupled)")

# Enable CORS for the frontend container
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
app.include_router(transfer.router, prefix="/transfer", tags=["transfer"])
app.include_router(batch.router, prefix="/batches", tags=["batches"])
