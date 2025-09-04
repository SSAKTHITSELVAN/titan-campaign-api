# customer_schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# Customer request models
class CustomerCreateRequest(BaseModel):
    email: EmailStr
    name: str
    description: Optional[str] = None
    category: Optional[str] = "subscriber"
    
    @validator('category')
    def validate_category(cls, v):
        if v and v not in ["subscriber", "lead", "customer", "prospect", "vip"]:
            raise ValueError('Invalid category. Must be one of: subscriber, lead, customer, prospect, vip')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class CustomerUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    
    @validator('category')
    def validate_category(cls, v):
        if v and v not in ["subscriber", "lead", "customer", "prospect", "vip"]:
            raise ValueError('Invalid category. Must be one of: subscriber, lead, customer, prospect, vip')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v

# Customer response models
class CustomerResponse(BaseModel):
    id: str
    company_id: str
    email: str
    name: str
    description: Optional[str] = None
    category: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Bulk operations
class CustomerBulkCreateRequest(BaseModel):
    customers: List[CustomerCreateRequest]
    
    @validator('customers')
    def validate_customers_list(cls, v):
        if not v:
            raise ValueError('Customers list cannot be empty')
        if len(v) > 100:  # Limit bulk operations
            raise ValueError('Cannot create more than 100 customers at once')
        return v

class CustomerBulkResponse(BaseModel):
    created: List[CustomerResponse]
    failed: List[dict]  # Contains error info for failed creations
    total_attempted: int
    total_created: int
    total_failed: int