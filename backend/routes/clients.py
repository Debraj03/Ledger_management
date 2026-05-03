from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from schemas import ClientCreate, ClientUpdate, ClientOut
from database import get_session
from auth import get_current_user
from crud import create_client, get_clients, get_client, update_client, delete_client
from typing import List

router = APIRouter()

@router.post("/", response_model=ClientOut)
def create_new_client(client: ClientCreate, db: Session = Depends(get_session), user=Depends(get_current_user)):
    return create_client(db, client)

@router.get("/", response_model=List[ClientOut])
def read_clients(db: Session = Depends(get_session), user=Depends(get_current_user)):
    return get_clients(db)

@router.get("/{client_id}", response_model=ClientOut)
def read_client(client_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    db_client = get_client(db, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.put("/{client_id}", response_model=ClientOut)
def update_client_profile(client_id: int, client: ClientUpdate, db: Session = Depends(get_session), user=Depends(get_current_user)):
    db_client = update_client(db, client_id, client)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.delete("/{client_id}")
def remove_client(client_id: int, db: Session = Depends(get_session), user=Depends(get_current_user)):
    db_client = delete_client(db, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"detail": "Client deleted"}
