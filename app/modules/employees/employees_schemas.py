from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    role: str  # admin, marketing, analyst
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ["admin", "marketing", "analyst"]:
            raise ValueError('Invalid role. Must be admin, marketing, or analyst')
        return v

class EmployeeCreate(EmployeeBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('role')
    def validate_role(cls, v):
        if v and v not in ["admin", "marketing", "analyst"]:
            raise ValueError('Invalid role. Must be admin, marketing, or analyst')
        return v

class EmployeeResponse(EmployeeBase):
    id: str  # Changed from int to str for UUID
    company_id: str  # Changed from int to str for UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v