### modules/tracking/services.py
from datetime import datetime
from sqlalchemy.orm import Session
from core.logger import logger
from database.models import CampaignRecipient
from .schemas import TrackingEvent, TrackingResponse

class TrackingService:
    def __init__(self, db: Session):
        self.db = db
    
    def track_open(self, campaign_id: int, recipient_id: int, user_agent: str = None, ip_address: str = None) -> TrackingResponse:
        """Track email open event"""
        try:
            recipient = self.db.query(CampaignRecipient).filter(
                CampaignRecipient.id == recipient_id,
                CampaignRecipient.campaign_id == campaign_id
            ).first()
            
            if not recipient:
                return TrackingResponse(success=False, message="Recipient not found")
            
            # Update opened timestamp if not already opened
            if recipient.opened_at is None:
                recipient.opened_at = datetime.utcnow()
                if recipient.status == "sent":
                    recipient.status = "opened"
                self.db.commit()
            
            logger.info(f"Email opened - Campaign: {campaign_id}, Recipient: {recipient_id}")
            return TrackingResponse(success=True, message="Open tracked successfully")
            
        except Exception as e:
            logger.error(f"Failed to track open event: {str(e)}")
            return TrackingResponse(success=False, message="Failed to track open")
    
    def track_click(self, campaign_id: int, recipient_id: int, url: str, user_agent: str = None, ip_address: str = None) -> TrackingResponse:
        """Track email click event"""
        try:
            recipient = self.db.query(CampaignRecipient).filter(
                CampaignRecipient.id == recipient_id,
                CampaignRecipient.campaign_id == campaign_id
            ).first()
            
            if not recipient:
                return TrackingResponse(success=False, message="Recipient not found")
            
            # Update clicked timestamp if not already clicked
            if recipient.clicked_at is None:
                recipient.clicked_at = datetime.utcnow()
                recipient.status = "clicked"
                
                # Also mark as opened if not already
                if recipient.opened_at is None:
                    recipient.opened_at = datetime.utcnow()
                
                self.db.commit()
            
            logger.info(f"Email clicked - Campaign: {campaign_id}, Recipient: {recipient_id}, URL: {url}")
            return TrackingResponse(success=True, message="Click tracked successfully")
            
        except Exception as e:
            logger.error(f"Failed to track click event: {str(e)}")
            return TrackingResponse(success=False, message="Failed to track click")
    
    def get_tracking_events(self, campaign_id: int) -> list:
        """Get all tracking events for a campaign"""
        recipients = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).all()
        
        events = []
        for recipient in recipients:
            if recipient.opened_at:
                events.append({
                    "recipient_id": recipient.id,
                    "event_type": "open",
                    "timestamp": recipient.opened_at
                })
            
            if recipient.clicked_at:
                events.append({
                    "recipient_id": recipient.id,
                    "event_type": "click",
                    "timestamp": recipient.clicked_at
                })
        
        return events
