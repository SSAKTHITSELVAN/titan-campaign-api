# # auth_schemas.py
# from pydantic import BaseModel, EmailStr, validator
# from typing import Optional
# from datetime import datetime

# # Response models
# class TokenVerifyResponse(BaseModel):
#     uid: str
#     email: str
#     is_new_user: bool = False

# class UserResponse(BaseModel):
#     uid: str
#     email: str
#     created_at: datetime
#     last_login: datetime
    
#     class Config:
#         from_attributes = True

# # Company request models
# class CompanyCreateRequest(BaseModel):
#     company_name: str
#     industry: Optional[str] = None
#     company_size: Optional[str] = None
#     website: Optional[str] = None
#     phone: Optional[str] = None
#     country: Optional[str] = None
#     timezone: Optional[str] = None
#     business_type: Optional[str] = None
#     description: Optional[str] = None
#     primary_use_case: Optional[str] = None
#     expected_monthly_emails: Optional[str] = None
    
#     @validator('company_size')
#     def validate_company_size(cls, v):
#         if v and v not in ["1-10", "11-50", "51-200", "201-1000", "1000+"]:
#             raise ValueError('Invalid company size')
#         return v
    
#     @validator('business_type')
#     def validate_business_type(cls, v):
#         if v and v not in ["B2B", "B2C", "B2B2C"]:
#             raise ValueError('Invalid business type')
#         return v
    
#     @validator('primary_use_case')
#     def validate_primary_use_case(cls, v):
#         if v and v not in ["newsletters", "promotions", "transactional", "all"]:
#             raise ValueError('Invalid primary use case')
#         return v
    
#     @validator('expected_monthly_emails')
#     def validate_expected_monthly_emails(cls, v):
#         if v and v not in ["0-1K", "1K-10K", "10K-50K", "50K+"]:
#             raise ValueError('Invalid expected monthly emails range')
#         return v

# class CompanyUpdateRequest(BaseModel):
#     company_name: Optional[str] = None
#     industry: Optional[str] = None
#     company_size: Optional[str] = None
#     website: Optional[str] = None
#     phone: Optional[str] = None
#     country: Optional[str] = None
#     timezone: Optional[str] = None
#     business_type: Optional[str] = None
#     description: Optional[str] = None
#     primary_use_case: Optional[str] = None
#     expected_monthly_emails: Optional[str] = None

# # Company response models
# class CompanyResponse(BaseModel):
#     id: str
#     user_uid: str
#     company_name: str
#     industry: Optional[str] = None
#     company_size: Optional[str] = None
#     website: Optional[str] = None
#     phone: Optional[str] = None
#     country: Optional[str] = None
#     timezone: Optional[str] = None
#     business_type: Optional[str] = None
#     description: Optional[str] = None
#     primary_use_case: Optional[str] = None
#     expected_monthly_emails: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime
    
#     class Config:
#         from_attributes = True



# auth_schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

# User request models
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

# User response models
class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

# Company request models
class CompanyCreateRequest(BaseModel):
    company_name: str
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
        if v and v not in ["newsletters", "promotions", "transactional", "all"]:
            raise ValueError('Invalid primary use case')
        return v
    
    @validator('expected_monthly_emails')
    def validate_expected_monthly_emails(cls, v):
        if v and v not in ["0-1K", "1K-10K", "10K-50K", "50K+"]:
            raise ValueError('Invalid expected monthly emails range')
        return v

class CompanyUpdateRequest(BaseModel):
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

# Company response models
class CompanyResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
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
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True