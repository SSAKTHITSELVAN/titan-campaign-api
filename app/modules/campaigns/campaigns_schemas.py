from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime

class CampaignBase(BaseModel):
    title: str
    subject: str
    body: str  # HTML content
    sender_email: EmailStr

class CampaignCreate(CampaignBase):
    # No recipient_ids in creation - keep it simple
    pass

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    sender_email: Optional[EmailStr] = None

class CampaignResponse(CampaignBase):
    id: str  # Changed from int to str for UUID
    company_id: str  # Changed from int to str for UUID
    status: str
    created_by_employee_id: str  # Changed from int to str for UUID
    recipient_count: Optional[int] = 0  # Add recipient count
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CampaignSend(BaseModel):
    recipient_ids: Optional[List[str]] = None  # Changed from List[int] to List[str] for UUID
    schedule_at: Optional[datetime] = None
    

class CampaignAddRecipients(BaseModel):
    recipient_ids: List[str]  # Changed from List[int] to List[str] for UUID

class CampaignStats(BaseModel):
    campaign_id: str  # Changed from int to str for UUID
    total_recipients: int
    sent_count: int
    opened_count: int
    clicked_count: int
    bounce_count: int
    open_rate: float
    click_rate: float

class CampaignRecipientStatus(BaseModel):
    """Schema for campaign recipient with status"""
    recipient_id: str  # Changed from int to str for UUID
    customer_id: str  # Changed from int to str for UUID
    customer_name: str
    customer_email: str
    status: str  # pending, sent, opened, clicked, failed, bounced
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True