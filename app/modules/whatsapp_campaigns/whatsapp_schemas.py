# from pydantic import BaseModel, validator
# from typing import List, Optional, Dict, Any
# from datetime import datetime

# class WhatsAppTemplateCreate(BaseModel):
#     name: str
#     language: str = "en_US"
#     category: str = "MARKETING"  # MARKETING, UTILITY, AUTHENTICATION
#     body: str
#     header: Optional[str] = None
#     footer: Optional[str] = None
#     buttons: Optional[List[Dict]] = None
    
#     @validator('name')
#     def validate_name(cls, v):
#         if not v or len(v) < 1:
#             raise ValueError("Template name is required")
#         # WhatsApp template names should be lowercase and use underscores
#         return v.lower().replace(' ', '_').replace('-', '_')
    
#     @validator('body')
#     def validate_body(cls, v):
#         if not v or len(v) > 1024:
#             raise ValueError("Body is required and must be less than 1024 characters")
#         return v

# class WhatsAppTemplateResponse(BaseModel):
#     id: str
#     company_id: str
#     name: str
#     language: str
#     category: str
#     status: str  # draft, submitted, approved, rejected
#     body: str
#     header: Optional[str]
#     footer: Optional[str]
#     buttons: Optional[List[Dict]]
#     created_at: datetime
    
#     class Config:
#         from_attributes = True

# class WhatsAppCampaignCreate(BaseModel):
#     title: str
#     template_id: str  # Reference to approved template
#     recipient_type: str = "customer_ids"  # customer_ids, all_customers, segment, tags
#     recipient_ids: Optional[List[str]] = None  # Customer IDs
#     segment_id: Optional[str] = None
#     tags: Optional[List[str]] = None
#     exclude_recipient_ids: Optional[List[str]] = None
#     schedule_at: Optional[datetime] = None
#     sender_phone_label: Optional[str] = None  # Phone number label to use

# class WhatsAppCampaignResponse(BaseModel):
#     id: str
#     company_id: str
#     title: str
#     channel: str
#     template_name: str
#     status: str
#     recipient_count: int = 0
#     sent_count: int = 0
#     delivered_count: int = 0
#     seen_count: int = 0
#     clicked_count: int = 0
#     failed_count: int = 0
#     scheduled_at: Optional[datetime]
#     sent_at: Optional[datetime]
#     created_at: datetime
    
#     class Config:
#         from_attributes = True

# class WhatsAppTestSend(BaseModel):
#     phone_number: str
#     template_name: str
    
#     @validator('phone_number')
#     def validate_phone(cls, v):
#         # Ensure phone number starts with + and country code
#         if not v.startswith('+'):
#             v = f"+{v}"
#         if len(v) < 8:
#             raise ValueError("Invalid phone number format")
#         return v

# class WhatsAppCampaignStats(BaseModel):
#     campaign_id: str
#     total_recipients: int
#     sent_count: int
#     delivered_count: int
#     seen_count: int
#     clicked_count: int
#     failed_count: int
#     delivery_rate: float
#     seen_rate: float
#     click_rate: float



from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class WhatsAppTemplateCreate(BaseModel):
    name: str
    language: str = "en_US"
    category: str = "MARKETING"  # MARKETING, UTILITY, AUTHENTICATION
    body: str
    header: Optional[str] = None
    footer: Optional[str] = None
    buttons: Optional[List[Dict]] = None
    
    # NEW FIELDS FOR MEDIA SUPPORT
    header_type: str = "text"  # text, image, video, document, location, none
    header_media_url: Optional[str] = None  # Public URL for media
    header_location_data: Optional[Dict] = None  # {latitude, longitude, name, address}
    body_parameters_count: int = 0  # Number of {{1}}, {{2}} in body text
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v) < 1:
            raise ValueError("Template name is required")
        # WhatsApp template names should be lowercase and use underscores
        return v.lower().replace(' ', '_').replace('-', '_')
    
    @validator('body')
    def validate_body(cls, v):
        if not v or len(v) > 1024:
            raise ValueError("Body is required and must be less than 1024 characters")
        return v
    
    @validator('header_type')
    def validate_header_type(cls, v):
        allowed_types = ["text", "image", "video", "document", "location", "none"]
        if v not in allowed_types:
            raise ValueError(f"Header type must be one of: {', '.join(allowed_types)}")
        return v
    
    @validator('header_media_url')
    def validate_media_url(cls, v, values):
        header_type = values.get('header_type', 'text')
        if header_type in ['image', 'video', 'document'] and not v:
            raise ValueError(f"Media URL is required for {header_type} header type")
        return v
    
    @validator('header_location_data')
    def validate_location_data(cls, v, values):
        header_type = values.get('header_type', 'text')
        if header_type == 'location':
            if not v or 'latitude' not in v or 'longitude' not in v:
                raise ValueError("Location data with latitude and longitude is required for location header")
        return v

class WhatsAppTemplateResponse(BaseModel):
    id: str
    company_id: str
    name: str
    language: str
    category: str
    status: str  # draft, submitted, approved, rejected
    body: str
    header: Optional[str]
    footer: Optional[str]
    buttons: Optional[List[Dict]]
    
    # NEW FIELDS
    header_type: str = "text"
    header_media_url: Optional[str] = None
    header_media_id: Optional[str] = None
    header_location_data: Optional[Dict] = None
    body_parameters_count: int = 0
    button_parameters: Optional[List[Dict]] = None
    meta_template_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True

class WhatsAppCampaignCreate(BaseModel):
    title: str
    template_id: str  # Reference to approved template
    recipient_type: str = "customer_ids"  # customer_ids, all_customers, segment, tags
    recipient_ids: Optional[List[str]] = None  # Customer IDs
    segment_id: Optional[str] = None
    tags: Optional[List[str]] = None
    exclude_recipient_ids: Optional[List[str]] = None
    schedule_at: Optional[datetime] = None
    sender_phone_label: Optional[str] = None  # Phone number label to use
    
    # NEW: Template parameter values for dynamic content
    body_parameters: Optional[List[str]] = None  # Values for {{1}}, {{2}}, etc.
    button_parameters: Optional[List[Dict]] = None  # Button URL parameters

class WhatsAppCampaignResponse(BaseModel):
    id: str
    company_id: str
    title: str
    channel: str
    template_name: str
    status: str
    recipient_count: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    seen_count: int = 0
    clicked_count: int = 0
    failed_count: int = 0
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class WhatsAppTestSend(BaseModel):
    phone_number: str
    template_name: str
    body_parameters: Optional[List[str]] = None  # For testing with parameters
    button_parameters: Optional[List[Dict]] = None
    
    @validator('phone_number')
    def validate_phone(cls, v):
        # Ensure phone number starts with + and country code
        if not v.startswith('+'):
            v = f"+{v}"
        if len(v) < 8:
            raise ValueError("Invalid phone number format")
        return v

class WhatsAppCampaignStats(BaseModel):
    campaign_id: str
    total_recipients: int
    sent_count: int
    delivered_count: int
    seen_count: int
    clicked_count: int
    failed_count: int
    delivery_rate: float
    seen_rate: float
    click_rate: float

class WhatsAppMediaUpload(BaseModel):
    file_path: str
    media_type: str  # image/jpeg, video/mp4, application/pdf, etc.
    
class WhatsAppMediaUploadResponse(BaseModel):
    media_id: str
    success: bool
    error: Optional[str] = None