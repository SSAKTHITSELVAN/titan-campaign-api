
### modules/campaigns/services.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from core.exceptions import ValidationError, EmailSendError
from core.logger import log_action
from database.models import Campaign, CampaignRecipient, Customer, Employee
from utils.email_service import email_service
from .schemas import (
    CampaignCreate, 
    CampaignUpdate, 
    CampaignResponse, 
    CampaignSend,
    CampaignStats
)

class CampaignService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(self, campaign_data: CampaignCreate, employee: Employee) -> CampaignResponse:
        campaign = Campaign(
            company_id=employee.company_id,
            created_by_employee_id=employee.id,
            **campaign_data.dict(exclude={"recipient_ids"})
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Add recipients if provided
        if campaign_data.recipient_ids:
            self._add_recipients(campaign.id, campaign_data.recipient_ids, employee)
        
        log_action(employee.id, "campaign_created", f"Created campaign: {campaign.title}")
        return CampaignResponse.from_orm(campaign)
    
    def get_campaigns(self, employee: Employee, skip: int = 0, limit: int = 100) -> List[CampaignResponse]:
        campaigns = self.db.query(Campaign).filter(
            Campaign.company_id == employee.company_id
        ).offset(skip).limit(limit).all()
        
        return [CampaignResponse.from_orm(campaign) for campaign in campaigns]
    
    def get_campaign(self, campaign_id: int, employee: Employee) -> CampaignResponse:
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        return CampaignResponse.from_orm(campaign)
    
    def update_campaign(
        self, 
        campaign_id: int, 
        campaign_data: CampaignUpdate, 
        employee: Employee
    ) -> CampaignResponse:
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        if campaign.status != "draft":
            raise ValidationError("Can only update draft campaigns")
        
        # Update fields
        for field, value in campaign_data.dict(exclude_unset=True).items():
            setattr(campaign, field, value)
        
        self.db.commit()
        self.db.refresh(campaign)
        
        log_action(employee.id, "campaign_updated", f"Updated campaign: {campaign.title}")
        return CampaignResponse.from_orm(campaign)
    
    def delete_campaign(self, campaign_id: int, employee: Employee) -> bool:
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        if campaign.status not in ["draft", "failed"]:
            raise ValidationError("Can only delete draft or failed campaigns")
        
        # Delete recipients first
        self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).delete()
        
        self.db.delete(campaign)
        self.db.commit()
        
        log_action(employee.id, "campaign_deleted", f"Deleted campaign: {campaign.title}")
        return True
    
    async def send_campaign(
        self, 
        campaign_id: int, 
        send_data: CampaignSend, 
        employee: Employee
    ) -> dict:
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        if campaign.status != "draft":
            raise ValidationError("Campaign already sent or in progress")
        
        # Add recipients
        self._add_recipients(campaign_id, send_data.recipient_ids, employee)
        
        # Get recipients with customer details
        recipients = self.db.query(CampaignRecipient, Customer).join(
            Customer, CampaignRecipient.customer_id == Customer.id
        ).filter(CampaignRecipient.campaign_id == campaign_id).all()
        
        if not recipients:
            raise ValidationError("No recipients found for campaign")
        
        # Update campaign status
        campaign.status = "sending"
        if send_data.schedule_at:
            campaign.scheduled_at = send_data.schedule_at
            campaign.status = "scheduled"
        
        self.db.commit()
        
        # Send emails immediately if not scheduled
        if not send_data.schedule_at:
            return await self._send_emails(campaign, recipients, employee)
        else:
            log_action(
                employee.id, 
                "campaign_scheduled", 
                f"Scheduled campaign {campaign.title} for {send_data.schedule_at}"
            )
            return {"message": "Campaign scheduled successfully"}
    
    async def _send_emails(self, campaign: Campaign, recipients: List, employee: Employee) -> dict:
        """Send emails to all recipients"""
        try:
            recipient_list = []
            for recipient, customer in recipients:
                recipient_list.append({
                    "email": customer.email,
                    "recipient_id": recipient.id
                })
            
            # Send bulk emails
            results = await email_service.send_bulk_emails(
                recipients=recipient_list,
                subject=campaign.subject,
                body=campaign.body,
                sender_email=campaign.sender_email,
                campaign_id=campaign.id
            )
            
            # Update campaign status
            campaign.status = "sent" if results["failed"] == 0 else "partial"
            campaign.sent_at = datetime.utcnow()
            
            # Update recipient statuses
            for recipient, customer in recipients:
                if customer.email not in [error.split(":")[0] for error in results["errors"]]:
                    recipient.status = "sent"
                    recipient.sent_at = datetime.utcnow()
            
            self.db.commit()
            
            log_action(
                employee.id, 
                "campaign_sent", 
                f"Campaign {campaign.title} sent to {results['sent']} recipients"
            )
            
            return {
                "message": "Campaign sent successfully",
                "results": results
            }
            
        except Exception as e:
            campaign.status = "failed"
            self.db.commit()
            log_action(employee.id, "campaign_failed", f"Campaign {campaign.title} failed: {str(e)}")
            raise EmailSendError(f"Failed to send campaign: {str(e)}")
    
    def _add_recipients(self, campaign_id: int, recipient_ids: List[int], employee: Employee):
        """Add recipients to campaign"""
        # Clear existing recipients
        self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).delete()
        
        # Add new recipients
        for customer_id in recipient_ids:
            # Verify customer belongs to company
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id,
                Customer.company_id == employee.company_id
            ).first()
            
            if customer:
                recipient = CampaignRecipient(
                    campaign_id=campaign_id,
                    customer_id=customer_id
                )
                self.db.add(recipient)
        
        self.db.commit()
    
    def get_campaign_stats(self, campaign_id: int, employee: Employee) -> CampaignStats:
        """Get campaign statistics"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        # Get recipient counts
        recipients = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).all()
        
        total_recipients = len(recipients)
        sent_count = len([r for r in recipients if r.status in ["sent", "opened", "clicked"]])
        opened_count = len([r for r in recipients if r.opened_at is not None])
        clicked_count = len([r for r in recipients if r.clicked_at is not None])
        bounce_count = len([r for r in recipients if r.status == "bounced"])
        
        open_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0
        click_rate = (clicked_count / sent_count * 100) if sent_count > 0 else 0
        
        return CampaignStats(
            campaign_id=campaign_id,
            total_recipients=total_recipients,
            sent_count=sent_count,
            opened_count=opened_count,
            clicked_count=clicked_count,
            bounce_count=bounce_count,
            open_rate=round(open_rate, 2),
            click_rate=round(click_rate, 2)
        )