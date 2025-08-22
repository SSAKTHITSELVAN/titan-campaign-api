
### modules/tracking/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TrackingEvent(BaseModel):
    campaign_id: int
    recipient_id: int
    event_type: str  # open, click
    timestamp: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class TrackingResponse(BaseModel):
    success: bool
    message: str

class ClickTrack(BaseModel):
    url: str
    campaign_id: int
    recipient_id: int