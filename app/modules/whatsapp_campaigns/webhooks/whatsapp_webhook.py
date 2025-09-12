from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import CampaignRecipient
from datetime import datetime
import os
import logging

whatsapp_webhook_router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "CHANGE_ME")
logger = logging.getLogger(__name__)

@whatsapp_webhook_router.get("/")
def verify_webhook(
    hub_mode: str = None, 
    hub_challenge: str = None, 
    hub_verify_token: str = None
):
    """Verify WhatsApp webhook"""
    if hub_verify_token == VERIFY_TOKEN and hub_mode == "subscribe":
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)
    
    logger.warning(f"Webhook verification failed: {hub_verify_token} != {VERIFY_TOKEN}")
    raise HTTPException(status_code=400, detail="Invalid verify token")

@whatsapp_webhook_router.post("/")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle WhatsApp webhook events"""
    try:
        payload = await request.json()
        logger.info(f"Webhook payload received: {payload}")
        
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Handle message status updates (delivered, read, failed)
                for status in value.get("statuses", []):
                    await _handle_status_update(db, status)
                
                # Handle interactive message responses (button clicks)
                for message in value.get("messages", []):
                    await _handle_message_response(db, message)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        # Always return 200 to acknowledge webhook receipt
        return {"success": False, "error": str(e)}

async def _handle_status_update(db: Session, status: dict):
    """Handle WhatsApp message status updates"""
    try:
        recipient_phone = status.get("recipient_id")
        message_status = status.get("status")
        timestamp = status.get("timestamp")
        message_id = status.get("id")
        
        if not recipient_phone or not message_status:
            return
        
        # Convert timestamp to datetime
        if timestamp:
            status_time = datetime.utcfromtimestamp(int(timestamp))
        else:
            status_time = datetime.utcnow()
        
        # Find recipient by phone number or message ID
        recipient = None
        if message_id:
            recipient = db.query(CampaignRecipient).filter(
                CampaignRecipient.message_id == message_id
            ).first()
        
        if not recipient and recipient_phone:
            recipient = db.query(CampaignRecipient).filter(
                CampaignRecipient.recipient_phone == recipient_phone
            ).order_by(CampaignRecipient.sent_at.desc()).first()
        
        if recipient:
            # Update status based on WhatsApp status
            if message_status == "delivered":
                recipient.delivered_at = status_time
                if recipient.status == "sent":
                    recipient.status = "delivered"
            
            elif message_status == "read":
                recipient.seen_at = status_time
                recipient.status = "seen"
            
            elif message_status == "failed":
                recipient.status = "failed"
            
            db.commit()
            logger.info(f"Updated recipient {recipient.id} status to {message_status}")
    
    except Exception as e:
        logger.error(f"Error handling status update: {str(e)}")

async def _handle_message_response(db: Session, message: dict):
    """Handle interactive message responses"""
    try:
        from_phone = message.get("from")
        message_type = message.get("type")
        
        if not from_phone:
            return
        
        # Handle button clicks
        if message_type == "button":
            button_data = message.get("button", {})
            
            # Find most recent recipient by phone
            recipient = db.query(CampaignRecipient).filter(
                CampaignRecipient.recipient_phone == from_phone
            ).order_by(CampaignRecipient.sent_at.desc()).first()
            
            if recipient:
                recipient.clicked = True
                recipient.clicked_at = datetime.utcnow()
                recipient.clicked_payload = button_data.get("payload") or button_data.get("text")
                recipient.status = "clicked"
                db.commit()
                logger.info(f"Recorded button click for recipient {recipient.id}")
        
        # Handle other interactive responses (quick replies, etc.)
        elif message_type == "interactive":
            interactive_data = message.get("interactive", {})
            
            recipient = db.query(CampaignRecipient).filter(
                CampaignRecipient.recipient_phone == from_phone
            ).order_by(CampaignRecipient.sent_at.desc()).first()
            
            if recipient:
                recipient.clicked = True
                recipient.clicked_at = datetime.utcnow()
                recipient.clicked_payload = str(interactive_data)
                recipient.status = "clicked"
                db.commit()
                logger.info(f"Recorded interactive response for recipient {recipient.id}")
    
    except Exception as e:
        logger.error(f"Error handling message response: {str(e)}")

