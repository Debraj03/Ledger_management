from sqlmodel import Session, select
from models import User, Client, Ledger
from auth import get_password_hash
from schemas import UserCreate, ClientCreate, ClientUpdate, LedgerCreate
import pandas as pd
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

def export_ledger_to_excel_and_clear(db: Session, client_id: int) -> BytesIO | None:
    ledgers = db.exec(
        select(Ledger).where(Ledger.client_id == client_id, Ledger.is_deleted == False)
    ).all()
    if not ledgers:
        return None
    
    utc = ZoneInfo("UTC")
    ist = ZoneInfo("Asia/Kolkata")

    def to_ist_str(dt: datetime | None) -> str:
        if not dt:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=utc)
        return dt.astimezone(ist).strftime("%Y-%m-%d %H:%M:%S")

    # Convert to DataFrame with IST datetime format
    df = pd.DataFrame([
        {
            "id": l.id,
            "quantity_kg": l.quantity_kg,
            "price_per_kg": l.price_per_kg,
            "total_price": l.total_price,
            "created_at": to_ist_str(l.created_at),
            "updated_at": to_ist_str(l.updated_at),
        } for l in ledgers
    ])
    
    # Export to BytesIO instead of file
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    
    for l in ledgers:
        db.delete(l)

    db.commit()
    return buffer

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
    payload = client.model_dump() if hasattr(client, "model_dump") else client.dict()
    db_client = Client(**payload)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_clients(db: Session):
    return db.exec(select(Client).where(Client.deleted_at == None)).all()

def get_client(db: Session, client_id: int):
    return db.exec(select(Client).where(Client.id == client_id, Client.deleted_at == None)).first()

def update_client(db: Session, client_id: int, client: ClientUpdate):
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    patch = (
        client.model_dump(exclude_unset=True)
        if hasattr(client, "model_dump")
        else client.dict(exclude_unset=True)
    )
    for field, value in patch.items():
        if value is not None:
            setattr(db_client, field, value)
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

    client = db.get(Client, client_id)
    if client is not None:
        client.total_amount = (client.total_amount or 0.0) + total_price
        client.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_ledger)
    return db_ledger

def create_ledgers_bulk(db: Session, client_id: int, ledgers: list[LedgerCreate]):
    created: list[Ledger] = []
    total_added = 0.0
    for entry in ledgers:
        total_price = entry.quantity_kg * entry.price_per_kg
        db_ledger = Ledger(
            quantity_kg=entry.quantity_kg,
            price_per_kg=entry.price_per_kg,
            total_price=total_price,
            client_id=client_id,
        )
        db.add(db_ledger)
        created.append(db_ledger)
        total_added += total_price

    client = db.get(Client, client_id)
    if client is not None:
        client.total_amount = (client.total_amount or 0.0) + total_added
        client.updated_at = datetime.utcnow()

    db.commit()
    for row in created:
        db.refresh(row)
    return created

def get_ledgers_by_client(db: Session, client_id: int):
    return db.exec(select(Ledger).where(Ledger.client_id == client_id, Ledger.is_deleted == False)).all()

def delete_ledger(db: Session, ledger_id: int):
    db_ledger = db.exec(select(Ledger).where(Ledger.id == ledger_id, Ledger.is_deleted == False)).first()
    if not db_ledger:
        return None
    db_ledger.is_deleted = True
    db_ledger.deleted_at = datetime.utcnow()
    db.commit()
    return db_ledger
