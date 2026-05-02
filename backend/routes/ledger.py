from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import LedgerCreate, LedgerOut
from database import get_session
from auth import get_current_user
from crud import create_ledger, get_ledgers_by_client, delete_ledger
from typing import List

router = APIRouter()

@router.post("/{client_id}", response_model=LedgerOut)
def add_ledger(client_id: int, ledger: LedgerCreate, db: Session = Depends(get_session), user=Depends(get_current_user)):
    return create_ledger(db, client_id, ledger)

@router.get("/{client_id}", response_model=List[LedgerOut])
def get_ledgers(client_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    return get_ledgers_by_client(db, client_id)

@router.delete("/delete/{ledger_id}")
def remove_ledger(ledger_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    db_ledger = delete_ledger(db, ledger_id)
    if not db_ledger:
        raise HTTPException(status_code=404, detail="Ledger not found")
    return {"detail": "Ledger deleted"}
