

### modules/campaigns/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class CampaignBase(BaseModel):
    title: str
    subject: str
    body: str
    sender_email: EmailStr

class CampaignCreate(CampaignBase):
    recipient_ids: Optional[List[int]] = []

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    sender_email: Optional[EmailStr] = None

class CampaignResponse(CampaignBase):
    id: int
    company_id: int
    status: str
    created_by_employee_id: int
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CampaignSend(BaseModel):
    recipient_ids: List[int]
    schedule_at: Optional[datetime] = None

class CampaignStats(BaseModel):
    campaign_id: int
    total_recipients: int
    sent_count: int
    opened_count: int
    clicked_count: int
    bounce_count: int
    open_rate: float
    click_rate: float
