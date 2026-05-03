from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    class Config:
        from_attributes = True

class LoginCred(BaseModel):
    username:str
    password:str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class ClientBase(BaseModel):
    name: str
    phone: str
    email: EmailStr

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]

class ClientOut(ClientBase):
    id: int
    total_amount: float
    created_at: datetime
    class Config:
        from_attributes = True

class LedgerBase(BaseModel):
    quantity_kg: float
    price_per_kg: float

class LedgerCreate(LedgerBase):
    pass

class LedgerOut(LedgerBase):
    id: int
    total_price: float
    created_at: datetime
    client_id: int
    class Config:
        from_attributes = True
