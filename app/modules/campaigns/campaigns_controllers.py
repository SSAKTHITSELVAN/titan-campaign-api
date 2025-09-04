from typing import List
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Employee
from utils.security import get_current_employee, require_role
from .campaigns_services import CampaignService
from .campaigns_schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignSend,
    CampaignAddRecipients,
    CampaignStats,
    CampaignRecipientStatus
)

campaigns_router = APIRouter()

@campaigns_router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Create a new campaign (draft status)"""
    service = CampaignService(db)
    return service.create_campaign(campaign_data, current_employee)

@campaigns_router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all campaigns with recipient counts"""
    service = CampaignService(db)
    return service.get_campaigns(current_employee, skip, limit)

@campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get single campaign with recipient count"""
    service = CampaignService(db)
    return service.get_campaign(campaign_id, current_employee)

@campaigns_router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,  # Changed from int to str for UUID
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Update campaign (only draft campaigns)"""
    service = CampaignService(db)
    return service.update_campaign(campaign_id, campaign_data, current_employee)

@campaigns_router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Delete campaign (only draft or failed campaigns)"""
    service = CampaignService(db)
    service.delete_campaign(campaign_id, current_employee)
    return {"message": "Campaign deleted successfully"}

@campaigns_router.post("/{campaign_id}/recipients")
async def add_recipients(
    campaign_id: str,  # Changed from int to str for UUID
    recipients_data: CampaignAddRecipients,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Add recipients to campaign (optional - can also be done during send)"""
    service = CampaignService(db)
    return service.add_recipients(campaign_id, recipients_data, current_employee)

@campaigns_router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,  # Changed from int to str for UUID
    send_data: CampaignSend = CampaignSend(),  # Default empty body
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """
    Send campaign:
    - If recipient_ids provided: send to those specific customers
    - If recipient_ids empty/null: send to all customers in company
    - If schedule_at provided: schedule for later, otherwise send immediately
    """
    service = CampaignService(db)
    result = await service.send_campaign(campaign_id, send_data, current_employee)
    return result

@campaigns_router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get campaign statistics (opens, clicks, etc.)"""
    service = CampaignService(db)
    return service.get_campaign_stats(campaign_id, current_employee)

@campaigns_router.get("/{campaign_id}/recipients", response_model=List[CampaignRecipientStatus])
async def get_campaign_recipients(
    campaign_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all recipients for a campaign with their status"""
    service = CampaignService(db)
    return service.get_campaign_recipients(campaign_id, current_employee)

# Tracking endpoint (no authentication needed - called by email clients)
@campaigns_router.get("/tracking/open/{campaign_id}/{recipient_id}")
async def track_email_open(
    campaign_id: str,  # Changed from int to str for UUID
    recipient_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db)
):
    """Track email open - returns 1x1 transparent pixel"""
    service = CampaignService(db)
    service.track_email_open(campaign_id, recipient_id)
    
    # Return 1x1 transparent pixel
    pixel_data = bytes.fromhex('47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b')
    return FastAPIResponse(content=pixel_data, media_type="image/gif")