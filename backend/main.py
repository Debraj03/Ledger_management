
from fastapi import FastAPI
from routes import auth, clients, ledger
from sqlmodel import SQLModel
from database import engine

app = FastAPI()

@app.on_event("startup")
def on_startup():
	SQLModel.metadata.create_all(engine)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(ledger.router, prefix="/ledger", tags=["ledger"])
