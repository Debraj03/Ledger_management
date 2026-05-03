from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from schemas import LedgerCreate, LedgerOut
from database import get_session
from auth import get_current_user
from crud import create_ledgers_bulk, get_ledgers_by_client, delete_ledger, export_ledger_to_excel_and_clear
from typing import List



router = APIRouter()

@router.post("/{client_id}", response_model=List[LedgerOut])
def add_ledgers(client_id: int, entries: List[LedgerCreate], db: Session = Depends(get_session), user=Depends(get_current_user)):
    return create_ledgers_bulk(db, client_id, entries)

@router.get("/{client_id}", response_model=List[LedgerOut])
def get_ledgers(client_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    return get_ledgers_by_client(db, client_id)

@router.delete("/delete/{ledger_id}", deprecated=True)
def remove_ledger(ledger_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    db_ledger = delete_ledger(db, ledger_id)
    if not db_ledger:
        raise HTTPException(status_code=404, detail="Ledger not found")
    return {"detail": "Ledger deleted"}

@router.get("/export/{client_id}")
def export_ledger(client_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    buffer = export_ledger_to_excel_and_clear(db, client_id)
    if not buffer:
        return {"detail": "No record found"}
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=client_{client_id}_ledger.xlsx"},
    )