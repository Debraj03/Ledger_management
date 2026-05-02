
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class TimeMixin(SQLModel):
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

class User(TimeMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

class Client(TimeMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    phone: str = Field(index=True)
    email: str = Field(index=True)
    ledgers: List["Ledger"] = Relationship(back_populates="client")

class Ledger(TimeMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    quantity_kg: float
    price_per_kg: float
    total_price: float
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional[Client] = Relationship(back_populates="ledgers")
    is_deleted: bool = Field(default=False)
