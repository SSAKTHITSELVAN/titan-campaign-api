from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    tags: List[str] = []

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None

class CustomerResponse(CustomerBase):
    id: str  # Changed from int to str for UUID
    company_id: str  # Changed from int to str for UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class CustomerImport(BaseModel):
    customers: List[CustomerCreate]