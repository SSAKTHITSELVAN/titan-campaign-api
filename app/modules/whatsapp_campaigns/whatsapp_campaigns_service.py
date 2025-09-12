from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import uuid
from core.exceptions import ValidationError
from core.logger import log_action
from database.models import Campaign, CampaignRecipient, Customer, Employee, WhatsAppTemplate, Segment
from utils.whatsapp_service import whatsapp_service

class WhatsAppCampaignService:
    def __init__(self, db: Session):
        self.db = db

    def create_campaign(self, campaign_data: dict, employee: Employee) -> Campaign:
        """Create WhatsApp campaign"""
        # Validate template exists and is approved
        template = self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.id == campaign_data['template_id'],
            WhatsAppTemplate.company_id == employee.company_id,
            WhatsAppTemplate.status == 'approved'
        ).first()
        
        if not template:
            raise ValidationError("Template not found or not approved")
        
        campaign = Campaign(
            id=str(uuid.uuid4())[:8],
            company_id=employee.company_id,
            created_by_employee_id=employee.id,
            title=campaign_data['title'],
            subject=campaign_data['title'],  # Use title as subject for WhatsApp
            body=template.body,
            sender_email=f"whatsapp_{employee.company_id}@system.local",
            status="draft",
            channel="whatsapp",
            template_name=template.name,
            scheduled_at=campaign_data.get('schedule_at'),
            created_at=datetime.utcnow()
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Add recipients based on type
        self._add_recipients_to_campaign(campaign, campaign_data, employee)
        
        log_action(employee.id, "whatsapp_campaign_created", f"Created WhatsApp campaign: {campaign.title}")
        return campaign
    
    def update_campaign(self, campaign_id: str, campaign_data: dict, employee: Employee) -> Campaign:
        """Update WhatsApp campaign (only draft campaigns)"""
        if not campaign_id or len(campaign_id) != 8:
            raise ValidationError("Invalid campaign ID format")
        
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).first()
        
        if not campaign:
            raise ValidationError("WhatsApp campaign not found")
        
        if campaign.status not in ["draft"]:
            raise ValidationError("Can only update draft campaigns")
        
        # Validate template exists if template_id changed
        if 'template_id' in campaign_data and campaign_data['template_id']:
            template = self.db.query(WhatsAppTemplate).filter(
                WhatsAppTemplate.id == campaign_data['template_id'],
                WhatsAppTemplate.company_id == employee.company_id,
                WhatsAppTemplate.status == 'approved'
            ).first()
            
            if not template:
                raise ValidationError("Template not found or not approved")
            
            campaign.template_name = template.name
            campaign.body = template.body
        
        # Update campaign fields
        if 'title' in campaign_data:
            campaign.title = campaign_data['title']
            campaign.subject = campaign_data['title']  # Keep subject in sync
        
        if 'schedule_at' in campaign_data:
            campaign.scheduled_at = campaign_data['schedule_at']
        
        # Clear existing recipients if recipient data changed
        recipient_fields = ['recipient_type', 'recipient_ids', 'segment_id', 'tags', 'exclude_recipient_ids']
        if any(field in campaign_data for field in recipient_fields):
            # Delete existing recipients
            self.db.query(CampaignRecipient).filter(
                CampaignRecipient.campaign_id == campaign_id
            ).delete()
            
            # Add new recipients
            self._add_recipients_to_campaign(campaign, campaign_data, employee)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        log_action(employee.id, "whatsapp_campaign_updated", f"Updated WhatsApp campaign: {campaign.title}")
        return campaign

    def delete_campaign(self, campaign_id: str, employee: Employee) -> Dict:
        """Delete WhatsApp campaign (only draft campaigns)"""
        if not campaign_id or len(campaign_id) != 8:
            raise ValidationError("Invalid campaign ID format")
        
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).first()
        
        if not campaign:
            raise ValidationError("WhatsApp campaign not found")
        
        if campaign.status not in ["draft"]:
            raise ValidationError("Can only delete draft campaigns")
        
        # Delete recipients first (foreign key constraint)
        self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).delete()
        
        # Delete campaign
        campaign_title = campaign.title
        self.db.delete(campaign)
        self.db.commit()
        
        log_action(employee.id, "whatsapp_campaign_deleted", f"Deleted WhatsApp campaign: {campaign_title}")
        
        return {
            "message": "Campaign deleted successfully",
            "campaign_id": campaign_id,
            "campaign_title": campaign_title
        }

    def duplicate_campaign(self, campaign_id: str, employee: Employee, new_title: Optional[str] = None) -> Campaign:
        """Duplicate existing WhatsApp campaign"""
        if not campaign_id or len(campaign_id) != 8:
            raise ValidationError("Invalid campaign ID format")
        
        original_campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).first()
        
        if not original_campaign:
            raise ValidationError("WhatsApp campaign not found")
        
        # Get original recipients
        original_recipients = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).all()
        
        # Create new campaign with duplicated data
        duplicate_title = new_title or f"{original_campaign.title} (Copy)"
        
        new_campaign = Campaign(
            id=str(uuid.uuid4())[:8],
            company_id=original_campaign.company_id,
            created_by_employee_id=employee.id,
            title=duplicate_title,
            subject=duplicate_title,
            body=original_campaign.body,
            sender_email=original_campaign.sender_email,
            status="draft",  # Always create as draft
            channel="whatsapp",
            template_name=original_campaign.template_name,
            scheduled_at=None,  # Clear scheduled time
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_campaign)
        self.db.commit()
        self.db.refresh(new_campaign)
        
        # Duplicate recipients
        for original_recipient in original_recipients:
            new_recipient = CampaignRecipient(
                id=str(uuid.uuid4())[:8],
                campaign_id=new_campaign.id,
                customer_id=original_recipient.customer_id,
                recipient_phone=original_recipient.recipient_phone,
                status="pending"  # Reset status
            )
            self.db.add(new_recipient)
        
        self.db.commit()
        
        log_action(
            employee.id, 
            "whatsapp_campaign_duplicated", 
            f"Duplicated WhatsApp campaign {original_campaign.title} as {duplicate_title}"
        )
        
        return new_campaign

    def _add_recipients_to_campaign(self, campaign: Campaign, campaign_data: dict, employee: Employee):
        """Add recipients to campaign based on type"""
        recipient_type = campaign_data.get('recipient_type', 'customer_ids')
        exclude_ids = campaign_data.get('exclude_recipient_ids', [])
        
        customers = []
        
        if recipient_type == 'customer_ids':
            # Specific customer IDs
            if campaign_data.get('recipient_ids'):
                customers = self.db.query(Customer).filter(
                    Customer.id.in_(campaign_data['recipient_ids']),
                    Customer.company_id == employee.company_id,
                    Customer.phone.isnot(None)
                ).all()
        
        elif recipient_type == 'all_customers':
            # All customers with phone numbers
            customers = self.db.query(Customer).filter(
                Customer.company_id == employee.company_id,
                Customer.phone.isnot(None)
            ).all()
        
        elif recipient_type == 'segment':
            # Customers in specific segment
            segment_id = campaign_data.get('segment_id')
            if segment_id:
                # This would require implementing segment logic
                # For now, just get all customers
                customers = self.db.query(Customer).filter(
                    Customer.company_id == employee.company_id,
                    Customer.phone.isnot(None)
                ).all()
        
        elif recipient_type == 'tags':
            # Customers with specific tags
            tags = campaign_data.get('tags', [])
            if tags:
                customers = self.db.query(Customer).filter(
                    Customer.company_id == employee.company_id,
                    Customer.phone.isnot(None),
                    Customer.tags.contains(tags)  # Assuming tags is JSON array
                ).all()
        
        # Filter out excluded customers
        if exclude_ids:
            customers = [c for c in customers if c.id not in exclude_ids]
        
        # Create campaign recipients
        for customer in customers:
            if customer.phone:  # Ensure phone number exists
                recipient = CampaignRecipient(
                    id=str(uuid.uuid4())[:8],
                    campaign_id=campaign.id,
                    customer_id=customer.id,
                    recipient_phone=customer.phone,
                    status="pending"
                )
                self.db.add(recipient)
        
        self.db.commit()

    # Update your whatsapp_campaigns_service.py send_campaign method

    def send_campaign(self, campaign_id: str, employee: Employee) -> Dict:
        """Send WhatsApp campaign with proper media handling"""
        if not campaign_id or len(campaign_id) != 8:
            raise ValidationError("Invalid campaign ID format")
        
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).first()
        
        if not campaign:
            raise ValidationError("WhatsApp campaign not found")
        
        if campaign.status not in ["draft"]:
            raise ValidationError("Campaign must be in draft status to send")
        
        # Get the template details for media handling
        template = self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.name == campaign.template_name,
            WhatsAppTemplate.company_id == employee.company_id
        ).first()
        
        if not template:
            raise ValidationError("Campaign template not found")
        
        # Get pending recipients with customer details
        recipients = self.db.query(CampaignRecipient, Customer).join(
            Customer, CampaignRecipient.customer_id == Customer.id
        ).filter(
            CampaignRecipient.campaign_id == campaign_id,
            CampaignRecipient.status == "pending"
        ).all()
        
        if not recipients:
            raise ValidationError("No recipients found for campaign")
        
        # Check if scheduled
        if campaign.scheduled_at and campaign.scheduled_at > datetime.utcnow():
            campaign.status = "scheduled"
            self.db.commit()
            return {"message": f"Campaign scheduled for {campaign.scheduled_at}"}
        
        # Send immediately
        campaign.status = "sending"
        self.db.commit()
        
        # Prepare phone numbers list
        phone_numbers = []
        recipient_map = {}  # Map phone to recipient for updating status
        
        for recipient, customer in recipients:
            if customer.phone:
                phone_numbers.append(customer.phone)
                recipient_map[customer.phone] = recipient
        
        # CRITICAL FIX: Prepare template parameters including button parameters
        template_params = {
            "header_type": template.header_type or "text",
            "header_content": template.header,
            "header_media_id": template.header_media_id,
            "header_media_url": template.header_media_url,
            "language_code": template.language or "en_US"
        }
        
        # Handle location header
        if template.header_type == "location" and template.header_location_data:
            template_params["header_content"] = template.header_location_data
        
        # CRITICAL FIX: Add button parameters if template has buttons
        if template.buttons:
            button_params = []
            for i, button in enumerate(template.buttons):
                if button.get("type") == "URL" and "{{1}}" in button.get("url", ""):
                    # Provide button parameter for URL buttons
                    button_params.append({
                        "sub_type": "url",
                        "index": i,
                        "parameters": [
                            {
                                "type": "text",
                                "text": ""  # Default value or get from campaign data
                            }
                        ]
                    })
            
            if button_params:
                template_params["button_parameters"] = button_params
        
        # Send bulk WhatsApp messages with proper template configuration
        results = whatsapp_service.send_bulk_template(
            phone_numbers,
            campaign.template_name,
            **template_params
        )
        
        # Update recipient statuses based on results
        for detail in results.get("details", []):
            phone = detail["phone"]
            status = detail["status"]
            
            if phone in recipient_map:
                recipient = recipient_map[phone]
                recipient.status = status
                
                if status == "sent":
                    recipient.sent_at = datetime.utcnow()
                    recipient.message_id = detail.get("message_id")
        
        # Update campaign status
        if results["failed"] == 0:
            campaign.status = "sent"
        else:
            campaign.status = "partial"
        
        campaign.sent_at = datetime.utcnow()
        self.db.commit()
        
        log_action(
            employee.id,
            "whatsapp_campaign_sent",
            f"Sent WhatsApp campaign {campaign.title}: {results['sent']} sent, {results['failed']} failed"
        )
        
        return {
            "message": "WhatsApp campaign sent",
            "campaign_id": campaign.id,
            "sent_count": results["sent"],
            "failed_count": results["failed"],
            "errors": results["errors"][:5],  # Limit errors in response
            "total_recipients": len(phone_numbers)
        }

   # Update your whatsapp_campaigns_service.py test_send method

    def test_send(self, phone_number: str, template_name: str, employee: Employee, body_parameters: List[str] = None, button_parameters: List[Dict] = None) -> Dict:
        """Send test WhatsApp message with proper media handling"""
        # Validate template exists and is approved
        template = self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.name == template_name,
            WhatsAppTemplate.company_id == employee.company_id,
            WhatsAppTemplate.status == 'approved'
        ).first()
        
        if not template:
            raise ValidationError(f"Approved template '{template_name}' not found")
        
        # CRITICAL FIX: Check if template needs media but doesn't have it
        if template.header_type in ["image", "video", "document"]:
            if not template.header_media_id and not template.header_media_url:
                return {
                    "message": "Template configuration error",
                    "phone_number": phone_number,
                    "template_name": template_name,
                    "success": False,
                    "error": f"Template '{template_name}' expects {template.header_type.upper()} header but no media configured. Please update template with media URL or upload media file.",
                    "template_config": {
                        "header_type": template.header_type,
                        "header_media_id": template.header_media_id,
                        "header_media_url": template.header_media_url,
                        "needs_media": True
                    }
                }
        
        # CRITICAL FIX: Check if template has buttons that need parameters
        button_params_to_send = button_parameters or []
        
        # If template has buttons and no button parameters provided, create default ones
        if template.buttons and not button_params_to_send:
            for i, button in enumerate(template.buttons):
                if button.get("type") == "URL" and "{{1}}" in button.get("url", ""):
                    # Provide default parameter for URL buttons
                    button_params_to_send.append({
                        "sub_type": "url",
                        "index": i,
                        "parameters": [{"type": "text", "text": ""}]  # Empty string as default
                    })
        
        # Prepare template parameters
        template_params = {
            "header_type": template.header_type or "text",
            "header_content": template.header,
            "header_media_id": template.header_media_id,
            "header_media_url": template.header_media_url,
            "language_code": template.language or "en_US",
            "body_parameters": body_parameters,
            "button_parameters": button_params_to_send
        }
        
        # Handle location header
        if template.header_type == "location" and template.header_location_data:
            template_params["header_content"] = template.header_location_data
        
        # Send test message with proper media handling
        result = whatsapp_service.send_template_message(
            phone_number,
            template_name,
            **template_params
        )
        
        log_action(
            employee.id,
            "whatsapp_test_sent",
            f"Sent test WhatsApp message to {phone_number} with template {template_name}"
        )
        
        return {
            "message": "Test message sent",
            "phone_number": phone_number,
            "template_name": template_name,
            "template_config": template_params,
            "success": result.get("success", False),
            "whatsapp_response": result.get("response"),
            "error": result.get("error"),
            "debug_payload": result.get("payload_sent")
        }
    def get_campaign_stats(self, campaign_id: str, employee: Employee) -> Dict:
        """Get campaign statistics"""
        if not campaign_id or len(campaign_id) != 8:
            raise ValidationError("Invalid campaign ID format")
        
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).first()
        
        if not campaign:
            raise ValidationError("WhatsApp campaign not found")
        
        # Get recipient statistics
        recipients = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).all()
        
        total_recipients = len(recipients)
        sent_count = len([r for r in recipients if r.status == "sent" or r.delivered_at])
        delivered_count = len([r for r in recipients if r.delivered_at])
        seen_count = len([r for r in recipients if r.seen_at])
        clicked_count = len([r for r in recipients if r.clicked])
        failed_count = len([r for r in recipients if r.status == "failed"])
        
        # Calculate rates
        delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
        seen_rate = (seen_count / delivered_count * 100) if delivered_count > 0 else 0
        click_rate = (clicked_count / delivered_count * 100) if delivered_count > 0 else 0
        
        return {
            "campaign_id": campaign_id,
            "total_recipients": total_recipients,
            "sent_count": sent_count,
            "delivered_count": delivered_count,
            "seen_count": seen_count,
            "clicked_count": clicked_count,
            "failed_count": failed_count,
            "delivery_rate": round(delivery_rate, 2),
            "seen_rate": round(seen_rate, 2),
            "click_rate": round(click_rate, 2)
        }

    def get_campaigns(self, employee: Employee, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get WhatsApp campaigns with stats"""
        campaigns = self.db.query(Campaign).filter(
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for campaign in campaigns:
            # Get recipient counts
            recipients = self.db.query(CampaignRecipient).filter(
                CampaignRecipient.campaign_id == campaign.id
            ).all()
            
            campaign_data = {
                "id": campaign.id,
                "company_id": campaign.company_id,
                "title": campaign.title,
                "channel": campaign.channel,
                "template_name": campaign.template_name,
                "status": campaign.status,
                "recipient_count": len(recipients),
                "sent_count": len([r for r in recipients if r.status == "sent" or r.delivered_at]),
                "delivered_count": len([r for r in recipients if r.delivered_at]),
                "seen_count": len([r for r in recipients if r.seen_at]),
                "clicked_count": len([r for r in recipients if r.clicked]),
                "failed_count": len([r for r in recipients if r.status == "failed"]),
                "scheduled_at": campaign.scheduled_at,
                "sent_at": campaign.sent_at,
                "created_at": campaign.created_at
            }
            result.append(campaign_data)
        
        return result