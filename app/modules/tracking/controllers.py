
### modules/tracking/controllers.py
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Employee
from utils.security import get_current_employee
from .services import TrackingService
from .schemas import TrackingResponse, ClickTrack

tracking_router = APIRouter()

@tracking_router.get("/open/{campaign_id}/{recipient_id}")
async def track_open(
    campaign_id: int,
    recipient_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track email open with 1x1 pixel"""
    service = TrackingService(db)
    
    # Get user agent and IP
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host
    
    # Track the open event
    service.track_open(campaign_id, recipient_id, user_agent, ip_address)
    
    # Return 1x1 transparent pixel
    pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
    
    return Response(
        content=pixel_data,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@tracking_router.get("/click/{campaign_id}/{recipient_id}")
async def track_click(
    campaign_id: int,
    recipient_id: int,
    url: str = Query(..., description="Original URL to redirect to"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Track email click and redirect to original URL"""
    service = TrackingService(db)
    
    # Get user agent and IP
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host
    
    # Track the click event
    service.track_click(campaign_id, recipient_id, url, user_agent, ip_address)
    
    # Redirect to original URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=url, status_code=302)

@tracking_router.get("/{campaign_id}/events")
async def get_tracking_events(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all tracking events for a campaign"""
    service = TrackingService(db)
    events = service.get_tracking_events(campaign_id)
    return {"campaign_id": campaign_id, "events": events}
