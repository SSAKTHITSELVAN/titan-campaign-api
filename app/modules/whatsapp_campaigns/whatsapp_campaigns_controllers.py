from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models import Employee
from utils.security import require_role, get_current_employee
from .whatsapp_campaigns_service import WhatsAppCampaignService
from .whatsapp_schemas import (
    WhatsAppCampaignCreate, 
    WhatsAppCampaignResponse, 
    WhatsAppTestSend,
    WhatsAppCampaignStats
)

whatsapp_campaigns_router = APIRouter()

@whatsapp_campaigns_router.post("/", response_model=WhatsAppCampaignResponse)
def create_whatsapp_campaign(
    campaign_data: WhatsAppCampaignCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Create a new WhatsApp campaign"""
    service = WhatsAppCampaignService(db)
    campaign = service.create_campaign(campaign_data.dict(), current_employee)
    
    # Convert to response format
    return WhatsAppCampaignResponse(
        id=campaign.id,
        company_id=campaign.company_id,
        title=campaign.title,
        channel=campaign.channel,
        template_name=campaign.template_name,
        status=campaign.status,
        recipient_count=len(campaign.recipients),
        scheduled_at=campaign.scheduled_at,
        sent_at=campaign.sent_at,
        created_at=campaign.created_at
    )

@whatsapp_campaigns_router.get("/", response_model=List[WhatsAppCampaignResponse])
def get_whatsapp_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all WhatsApp campaigns with statistics"""
    service = WhatsAppCampaignService(db)
    campaigns = service.get_campaigns(current_employee, skip, limit)
    
    # Convert to response format
    response = []
    for campaign_data in campaigns:
        response.append(WhatsAppCampaignResponse(**campaign_data))
    
    return response

@whatsapp_campaigns_router.get("/{campaign_id}", response_model=WhatsAppCampaignResponse)
def get_whatsapp_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get single WhatsApp campaign"""
    service = WhatsAppCampaignService(db)
    campaigns = service.get_campaigns(current_employee)
    
    campaign_data = next((c for c in campaigns if c["id"] == campaign_id), None)
    if not campaign_data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return WhatsAppCampaignResponse(**campaign_data)


@whatsapp_campaigns_router.put("/{campaign_id}", response_model=WhatsAppCampaignResponse)
def update_whatsapp_campaign(
    campaign_id: str,
    campaign_data: WhatsAppCampaignCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Update WhatsApp campaign (only draft campaigns)"""
    service = WhatsAppCampaignService(db)
    campaign = service.update_campaign(campaign_id, campaign_data.dict(), current_employee)
    
    # Convert to response format
    return WhatsAppCampaignResponse(
        id=campaign.id,
        company_id=campaign.company_id,
        title=campaign.title,
        channel=campaign.channel,
        template_name=campaign.template_name,
        status=campaign.status,
        recipient_count=len(campaign.recipients),
        scheduled_at=campaign.scheduled_at,
        sent_at=campaign.sent_at,
        created_at=campaign.created_at
    )

@whatsapp_campaigns_router.delete("/{campaign_id}")
def delete_whatsapp_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Delete WhatsApp campaign (only draft campaigns)"""
    service = WhatsAppCampaignService(db)
    result = service.delete_campaign(campaign_id, current_employee)
    return result

@whatsapp_campaigns_router.post("/{campaign_id}/duplicate", response_model=WhatsAppCampaignResponse)
def duplicate_whatsapp_campaign(
    campaign_id: str,
    new_title: Optional[str] = None,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Duplicate existing WhatsApp campaign"""
    service = WhatsAppCampaignService(db)
    campaign = service.duplicate_campaign(campaign_id, current_employee, new_title)
    
    # Convert to response format
    return WhatsAppCampaignResponse(
        id=campaign.id,
        company_id=campaign.company_id,
        title=campaign.title,
        channel=campaign.channel,
        template_name=campaign.template_name,
        status=campaign.status,
        recipient_count=len(campaign.recipients),
        scheduled_at=campaign.scheduled_at,
        sent_at=campaign.sent_at,
        created_at=campaign.created_at
    )

@whatsapp_campaigns_router.post("/{campaign_id}/send")
def send_whatsapp_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Send WhatsApp campaign"""
    service = WhatsAppCampaignService(db)
    result = service.send_campaign(campaign_id, current_employee)
    return result

@whatsapp_campaigns_router.post("/test-send")
def test_send_whatsapp(
    test_data: WhatsAppTestSend,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Send test WhatsApp message"""
    service = WhatsAppCampaignService(db)
    result = service.test_send(test_data.phone_number, test_data.template_name, current_employee)
    return result

@whatsapp_campaigns_router.get("/{campaign_id}/stats", response_model=WhatsAppCampaignStats)
def get_campaign_stats(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get detailed campaign statistics"""
    service = WhatsAppCampaignService(db)
    stats = service.get_campaign_stats(campaign_id, current_employee)
    return WhatsAppCampaignStats(**stats)

@whatsapp_campaigns_router.get("/{campaign_id}/recipients")
def get_campaign_recipients(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get campaign recipients with their delivery status"""
    from database.models import Campaign, CampaignRecipient, Customer
    
    # Validate campaign exists and belongs to company
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.company_id == current_employee.company_id,
        Campaign.channel == "whatsapp"
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="WhatsApp campaign not found")
    
    # Get recipients with customer details
    recipients_data = db.query(CampaignRecipient, Customer).join(
        Customer, CampaignRecipient.customer_id == Customer.id
    ).filter(
        CampaignRecipient.campaign_id == campaign_id
    ).all()
    
    result = []
    for recipient, customer in recipients_data:
        result.append({
            "recipient_id": recipient.id,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "customer_email": customer.email,
            "phone_number": customer.phone,
            "status": recipient.status,
            "sent_at": recipient.sent_at,
            "delivered_at": recipient.delivered_at,
            "seen_at": recipient.seen_at,
            "clicked": recipient.clicked,
            "clicked_at": recipient.clicked_at,
            "message_id": recipient.message_id
        })
    
    return result
