from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document: str = Field(index=True, unique=True)
    full_name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    phone: str = "999999999"
    address: str = "Huancayo, Peru"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    account_number: str = Field(index=True, unique=True)
    account_type: str = "Cuenta Ahorro"
    currency: str = "PEN"
    balance: float = 0.0
    status: str = "activa"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Movement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id")
    description: str
    operation_type: str
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CreditApplication(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    product: str = "Prestamo Personal BanBif"
    amount: float
    months: int
    monthly_income: float
    purpose: str
    status: str = "enviado"
    analyst_comment: str = "Solicitud recibida correctamente."
    created_at: datetime = Field(default_factory=datetime.utcnow)
