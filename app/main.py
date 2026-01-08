from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import models, db
from app.api import users, wallets, transfer, batch
from fastapi.responses import FileResponse

# Create tables
models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(title="Wallet Engine (Build Phase)")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
app.include_router(transfer.router, prefix="/transfer", tags=["transfer"])
app.include_router(batch.router, prefix="/batches", tags=["batches"])

# Serve UI
app.mount("/static", StaticFiles(directory="ui"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('ui/index.html')
