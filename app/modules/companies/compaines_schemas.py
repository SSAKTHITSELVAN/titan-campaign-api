from pydantic import BaseModel, EmailStr, HttpUrl, validator
from typing import Optional, Dict, Any
from datetime import datetime

class CompanyBase(BaseModel):
    company_name: str
    domain: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    business_type: Optional[str] = None
    description: Optional[str] = None
    primary_use_case: Optional[str] = None
    expected_monthly_emails: Optional[str] = None

class CompanyCreate(CompanyBase):
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    
    @validator('company_size')
    def validate_company_size(cls, v):
        if v and v not in ["1-10", "11-50", "51-200", "201-1000", "1000+"]:
            raise ValueError('Invalid company size')
        return v
    
    @validator('business_type')
    def validate_business_type(cls, v):
        if v and v not in ["B2B", "B2C", "B2B2C"]:
            raise ValueError('Invalid business type')
        return v
    
    @validator('primary_use_case')
    def validate_primary_use_case(cls, v):
        if v and v not in ["newsletters", "marketing", "transactional", "mixed"]:
            raise ValueError('Invalid primary use case')
        return v
    
    @validator('expected_monthly_emails')
    def validate_expected_monthly_emails(cls, v):
        if v and v not in ["0-1K", "1K-10K", "10K-50K", "50K-100K", "100K-500K", "500K+"]:
            raise ValueError('Invalid expected monthly emails range')
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v or '.' not in v:
            raise ValueError('Invalid domain format')
        return v.lower()

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    business_type: Optional[str] = None
    description: Optional[str] = None
    primary_use_case: Optional[str] = None
    expected_monthly_emails: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    
    @validator('company_size')
    def validate_company_size(cls, v):
        if v and v not in ["1-10", "11-50", "51-200", "201-1000", "1000+"]:
            raise ValueError('Invalid company size')
        return v
    
    @validator('business_type')
    def validate_business_type(cls, v):
        if v and v not in ["B2B", "B2C", "B2B2C"]:
            raise ValueError('Invalid business type')
        return v
    
    @validator('primary_use_case')
    def validate_primary_use_case(cls, v):
        if v and v not in ["newsletters", "marketing", "transactional", "mixed"]:
            raise ValueError('Invalid primary use case')
        return v

class CompanyResponse(CompanyBase):
    id: str  # Changed from int to str for UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = {}
    
    # Employee count (will be populated by service)
    employee_count: Optional[int] = None
    customer_count: Optional[int] = None
    campaign_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class CompanyStats(BaseModel):
    company_id: str  # Changed from int to str for UUID
    employee_count: int
    customer_count: int
    campaign_count: int
    total_emails_sent: int
    current_month_emails: int
    
    # Usage statistics
    storage_used_mb: float
    last_activity: Optional[datetime] = None

class CompanySettings(BaseModel):
    """Company-specific email and system settings"""
    sender_name: Optional[str] = None
    reply_to_email: Optional[str] = None
    smtp_settings: Optional[Dict[str, str]] = None
    branding: Optional[Dict[str, str]] = None
    email_templates: Optional[Dict[str, str]] = None
    notifications: Optional[Dict[str, bool]] = None