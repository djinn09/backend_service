from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

# SIP Schemas
class SIPBase(BaseModel):
    scheme_name: str
    monthly_amount: float
    start_date: date

class SIPCreate(SIPBase):
    pass

class SIP(SIPBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class SIPSummary(BaseModel):
    scheme_name: str
    total_invested: float
    months_invested: int
