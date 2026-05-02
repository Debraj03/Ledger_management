from sqlalchemy.orm import Session
from models import User, Client, Ledger
from auth import get_password_hash
from schemas import UserCreate, ClientCreate, ClientUpdate, LedgerCreate
from datetime import datetime

def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_client(db: Session, client: ClientCreate):
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_clients(db: Session):
    return db.query(Client).filter(Client.deleted_at == None).all()

def get_client(db: Session, client_id: int):
    return db.query(Client).filter(Client.id == client_id, Client.deleted_at == None).first()

def update_client(db: Session, client_id: int, client: ClientUpdate):
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    for var, value in vars(client).items():
        if value is not None:
            setattr(db_client, var, value)
    db_client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: int):
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    db_client.deleted_at = datetime.utcnow()
    db.commit()
    return db_client

def create_ledger(db: Session, client_id: int, ledger: LedgerCreate):
    total_price = ledger.quantity_kg * ledger.price_per_kg
    db_ledger = Ledger(
        quantity_kg=ledger.quantity_kg,
        price_per_kg=ledger.price_per_kg,
        total_price=total_price,
        client_id=client_id
    )
    db.add(db_ledger)
    db.commit()
    db.refresh(db_ledger)
    return db_ledger

def get_ledgers_by_client(db: Session, client_id: int):
    return db.query(Ledger).filter(Ledger.client_id == client_id, Ledger.is_deleted == False).all()

def delete_ledger(db: Session, ledger_id: int):
    db_ledger = db.query(Ledger).filter(Ledger.id == ledger_id, Ledger.is_deleted == False).first()
    if not db_ledger:
        return None
    db_ledger.is_deleted = True
    db_ledger.deleted_at = datetime.utcnow()
    db.commit()
    return db_ledger
