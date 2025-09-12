# from typing import List
# from fastapi import APIRouter, Depends, Query, Response
# from fastapi.responses import Response as FastAPIResponse
# from sqlalchemy.orm import Session
# from database.connection import get_db
# from database.models import Employee
# from utils.security import get_current_employee, require_role
# from .campaigns_services import CampaignService
# # from utils.whatsapp_service import whatsapp_service
# from .campaigns_schemas import (
#     CampaignCreate,
#     CampaignUpdate,
#     CampaignResponse,
#     CampaignSend,
#     CampaignAddRecipients,
#     CampaignStats,
#     CampaignRecipientStatus
# )

# campaigns_router = APIRouter()

# @campaigns_router.post("/", response_model=CampaignResponse)
# async def create_campaign(
#     campaign_data: CampaignCreate,
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(require_role(["admin", "marketing"]))
# ):
#     """Create a new campaign (draft status)"""
#     service = CampaignService(db)
#     return service.create_campaign(campaign_data, current_employee)

# @campaigns_router.get("/", response_model=List[CampaignResponse])
# async def get_campaigns(
#     skip: int = Query(0, ge=0),
#     limit: int = Query(100, ge=1, le=1000),
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(get_current_employee)
# ):
#     """Get all campaigns with recipient counts"""
#     service = CampaignService(db)
#     return service.get_campaigns(current_employee, skip, limit)

# @campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
# async def get_campaign(
#     campaign_id: str,  # Changed from int to str for UUID
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(get_current_employee)
# ):
#     """Get single campaign with recipient count"""
#     service = CampaignService(db)
#     return service.get_campaign(campaign_id, current_employee)

# @campaigns_router.put("/{campaign_id}", response_model=CampaignResponse)
# async def update_campaign(
#     campaign_id: str,  # Changed from int to str for UUID
#     campaign_data: CampaignUpdate,
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(require_role(["admin", "marketing"]))
# ):
#     """Update campaign (only draft campaigns)"""
#     service = CampaignService(db)
#     return service.update_campaign(campaign_id, campaign_data, current_employee)

# @campaigns_router.delete("/{campaign_id}")
# async def delete_campaign(
#     campaign_id: str,  # Changed from int to str for UUID
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(require_role(["admin", "marketing"]))
# ):
#     """Delete campaign (only draft or failed campaigns)"""
#     service = CampaignService(db)
#     service.delete_campaign(campaign_id, current_employee)
#     return {"message": "Campaign deleted successfully"}

# @campaigns_router.post("/{campaign_id}/recipients")
# async def add_recipients(
#     campaign_id: str,  # Changed from int to str for UUID
#     recipients_data: CampaignAddRecipients,
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(require_role(["admin", "marketing"]))
# ):
#     """Add recipients to campaign (optional - can also be done during send)"""
#     service = CampaignService(db)
#     return service.add_recipients(campaign_id, recipients_data, current_employee)

# @campaigns_router.post("/{campaign_id}/send")
# async def send_campaign(
#     campaign_id: str,  # Changed from int to str for UUID
#     send_data: CampaignSend = CampaignSend(),  # Default empty body
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(require_role(["admin", "marketing"]))
# ):
#     """
#     Send campaign:
#     - If recipient_ids provided: send to those specific customers
#     - If recipient_ids empty/null: send to all customers in company
#     - If schedule_at provided: schedule for later, otherwise send immediately
#     """
#     service = CampaignService(db)
#     result = await service.send_campaign(campaign_id, send_data, current_employee)
#     return result

# @campaigns_router.get("/{campaign_id}/stats", response_model=CampaignStats)
# async def get_campaign_stats(
#     campaign_id: str,  # Changed from int to str for UUID
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(get_current_employee)
# ):
#     """Get campaign statistics (opens, clicks, etc.)"""
#     service = CampaignService(db)
#     return service.get_campaign_stats(campaign_id, current_employee)

# @campaigns_router.get("/{campaign_id}/recipients", response_model=List[CampaignRecipientStatus])
# async def get_campaign_recipients(
#     campaign_id: str,  # Changed from int to str for UUID
#     db: Session = Depends(get_db),
#     current_employee: Employee = Depends(get_current_employee)
# ):
#     """Get all recipients for a campaign with their status"""
#     service = CampaignService(db)
#     return service.get_campaign_recipients(campaign_id, current_employee)

# # Tracking endpoint (no authentication needed - called by email clients)
# @campaigns_router.get("/tracking/open/{campaign_id}/{recipient_id}")
# async def track_email_open(
#     campaign_id: str,  # Changed from int to str for UUID
#     recipient_id: str,  # Changed from int to str for UUID
#     db: Session = Depends(get_db)
# ):
#     """Track email open - returns 1x1 transparent pixel"""
#     service = CampaignService(db)
#     service.track_email_open(campaign_id, recipient_id)
    
#     # Return 1x1 transparent pixel
#     pixel_data = bytes.fromhex('47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b')
#     return FastAPIResponse(content=pixel_data, media_type="image/gif")

# # @campaigns_router.post("/whatsapp/send-test")
# # async def send_test_whatsapp(phone: str, template_name: str = "hello_world"):
# #     result = whatsapp_service.send_template_message(phone, template_name)
# #     return {"status": "ok", "response": result}


# Fix for campaigns_controllers.py - likely the issue is UUID foreign key mismatch

from typing import List
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.connection import get_db
from database.models import Employee, Campaign, CampaignRecipient
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
    try:
        service = CampaignService(db)
        return service.create_campaign(campaign_data, current_employee)
    except Exception as e:
        import traceback
        print(f"Error in create_campaign: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")

@campaigns_router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all campaigns with recipient counts"""
    try:
        # Direct query approach with error handling
        campaigns_query = db.query(
            Campaign,
            func.count(CampaignRecipient.id).label('recipient_count')
        ).outerjoin(
            CampaignRecipient, Campaign.id == CampaignRecipient.campaign_id
        ).filter(
            Campaign.company_id == current_employee.company_id,
            # Only get email campaigns, exclude WhatsApp campaigns
            Campaign.channel.in_(['email', None])
        ).group_by(Campaign.id).order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for campaign, recipient_count in campaigns_query:
            try:
                campaign_response = CampaignResponse.from_orm(campaign)
                campaign_response.recipient_count = recipient_count or 0
                result.append(campaign_response)
            except Exception as e:
                print(f"Error processing campaign {campaign.id}: {str(e)}")
                # Skip problematic campaigns instead of failing entirely
                continue
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error in get_campaigns: {str(e)}")
        print(traceback.format_exc())
        
        # Fallback to service method
        try:
            service = CampaignService(db)
            return service.get_campaigns(current_employee, skip, limit)
        except Exception as service_error:
            print(f"Service method also failed: {str(service_error)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve campaigns")

@campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get single campaign with recipient count"""
    try:
        service = CampaignService(db)
        return service.get_campaign(campaign_id, current_employee)
    except Exception as e:
        import traceback
        print(f"Error in get_campaign {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=404, detail="Campaign not found")

@campaigns_router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Update campaign (only draft campaigns)"""
    try:
        service = CampaignService(db)
        return service.update_campaign(campaign_id, campaign_data, current_employee)
    except Exception as e:
        import traceback
        print(f"Error in update_campaign {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@campaigns_router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Delete campaign (only draft or failed campaigns)"""
    try:
        service = CampaignService(db)
        service.delete_campaign(campaign_id, current_employee)
        return {"message": "Campaign deleted successfully"}
    except Exception as e:
        import traceback
        print(f"Error in delete_campaign {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@campaigns_router.post("/{campaign_id}/recipients")
async def add_recipients(
    campaign_id: str,
    recipients_data: CampaignAddRecipients,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Add recipients to campaign (optional - can also be done during send)"""
    try:
        service = CampaignService(db)
        return service.add_recipients(campaign_id, recipients_data, current_employee)
    except Exception as e:
        import traceback
        print(f"Error in add_recipients {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@campaigns_router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    send_data: CampaignSend = CampaignSend(),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """
    Send campaign:
    - If recipient_ids provided: send to those specific customers
    - If recipient_ids empty/null: send to all customers in company
    - If schedule_at provided: schedule for later, otherwise send immediately
    """
    try:
        service = CampaignService(db)
        result = await service.send_campaign(campaign_id, send_data, current_employee)
        return result
    except Exception as e:
        import traceback
        print(f"Error in send_campaign {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@campaigns_router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get campaign statistics (opens, clicks, etc.)"""
    try:
        service = CampaignService(db)
        return service.get_campaign_stats(campaign_id, current_employee)
    except Exception as e:
        import traceback
        print(f"Error in get_campaign_stats {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=404, detail="Campaign not found")

@campaigns_router.get("/{campaign_id}/recipients", response_model=List[CampaignRecipientStatus])
async def get_campaign_recipients(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all recipients for a campaign with their status"""
    try:
        service = CampaignService(db)
        return service.get_campaign_recipients(campaign_id, current_employee)
    except Exception as e:
        import traceback
        print(f"Error in get_campaign_recipients {campaign_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=404, detail="Campaign not found")

# Tracking endpoint (no authentication needed - called by email clients)
@campaigns_router.get("/tracking/open/{campaign_id}/{recipient_id}")
async def track_email_open(
    campaign_id: str,
    recipient_id: str,
    db: Session = Depends(get_db)
):
    """Track email open - returns 1x1 transparent pixel"""
    try:
        service = CampaignService(db)
        service.track_email_open(campaign_id, recipient_id)
    except Exception as e:
        # Silently fail for tracking - don't break email display
        print(f"Tracking error for campaign {campaign_id}, recipient {recipient_id}: {str(e)}")
    
    # Always return pixel regardless of success/failure
    pixel_data = bytes.fromhex('47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b')
    return FastAPIResponse(content=pixel_data, media_type="image/gif")

# Debug endpoint to help diagnose database issues
@campaigns_router.get("/debug/database-info")
async def debug_database_info(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    """Debug endpoint to check database schema and constraints"""
    try:
        # Check if we can query basic tables
        campaign_count = db.query(Campaign).filter(Campaign.company_id == current_employee.company_id).count()
        recipient_count = db.query(CampaignRecipient).count()
        
        # Check for any campaigns with NULL channels (old data)
        null_channel_campaigns = db.query(Campaign).filter(
            Campaign.company_id == current_employee.company_id,
            Campaign.channel.is_(None)
        ).count()
        
        whatsapp_campaigns = db.query(Campaign).filter(
            Campaign.company_id == current_employee.company_id,
            Campaign.channel == "whatsapp"
        ).count()
        
        email_campaigns = db.query(Campaign).filter(
            Campaign.company_id == current_employee.company_id,
            Campaign.channel == "email"
        ).count()
        
        return {
            "company_id": current_employee.company_id,
            "total_campaigns": campaign_count,
            "total_recipients": recipient_count,
            "null_channel_campaigns": null_channel_campaigns,
            "whatsapp_campaigns": whatsapp_campaigns,
            "email_campaigns": email_campaigns,
            "database_connection": "OK"
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "database_connection": "FAILED"
        }