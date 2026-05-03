
from fastapi import FastAPI
from routes import auth, clients, ledger
from sqlmodel import SQLModel
from database import engine
from sqlalchemy import text

app = FastAPI()

@app.on_event("startup")
def on_startup():

	SQLModel.metadata.create_all(engine)

	# Lightweight migration for local SQLite dev DBs
	with engine.begin() as conn:
		tables = {row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()}

		if "client" in tables and "clients" not in tables:
			conn.execute(text("ALTER TABLE client RENAME TO clients"))
		if "ledger" in tables and "ledgers" not in tables:
			conn.execute(text("ALTER TABLE ledger RENAME TO ledgers"))

		cols = conn.execute(text("PRAGMA table_info(clients)")).fetchall()
		col_names = {row[1] for row in cols}
		if "total_amount" not in col_names:
			conn.execute(text("ALTER TABLE clients ADD COLUMN total_amount FLOAT DEFAULT 0.0"))

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(ledger.router, prefix="/ledger", tags=["ledger"])
