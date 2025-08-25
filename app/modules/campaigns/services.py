# from typing import List, Optional
# from datetime import datetime
# from sqlalchemy.orm import Session
# from sqlalchemy import func
# from core.exceptions import ValidationError, EmailSendError
# from core.logger import log_action
# from database.models import Campaign, CampaignRecipient, Customer, Employee
# from utils.email_service import email_service
# from .schemas import (
#     CampaignCreate, 
#     CampaignUpdate, 
#     CampaignResponse, 
#     CampaignSend,
#     CampaignAddRecipients,
#     CampaignStats
# )

# class CampaignService:
#     def __init__(self, db: Session):
#         self.db = db
    
#     def create_campaign(self, campaign_data: CampaignCreate, employee: Employee) -> CampaignResponse:
#         """Create a new campaign (without recipients initially)"""
#         campaign = Campaign(
#             company_id=employee.company_id,
#             created_by_employee_id=employee.id,
#             status="draft",
#             **campaign_data.dict()
#         )
        
#         self.db.add(campaign)
#         self.db.commit()
#         self.db.refresh(campaign)
        
#         log_action(employee.id, "campaign_created", f"Created campaign: {campaign.title}")
        
#         # Get recipient count (0 initially)
#         response_data = CampaignResponse.from_orm(campaign)
#         response_data.recipient_count = 0
#         return response_data
    
#     def get_campaigns(self, employee: Employee, skip: int = 0, limit: int = 100) -> List[CampaignResponse]:
#         """Get all campaigns with recipient counts"""
#         campaigns_query = self.db.query(
#             Campaign,
#             func.count(CampaignRecipient.id).label('recipient_count')
#         ).outerjoin(
#             CampaignRecipient, Campaign.id == CampaignRecipient.campaign_id
#         ).filter(
#             Campaign.company_id == employee.company_id
#         ).group_by(Campaign.id).offset(skip).limit(limit).all()
        
#         result = []
#         for campaign, recipient_count in campaigns_query:
#             campaign_response = CampaignResponse.from_orm(campaign)
#             campaign_response.recipient_count = recipient_count or 0
#             result.append(campaign_response)
        
#         return result
    
#     def get_campaign(self, campaign_id: int, employee: Employee) -> CampaignResponse:
#         """Get single campaign with recipient count"""
#         campaign = self.db.query(Campaign).filter(
#             Campaign.id == campaign_id,
#             Campaign.company_id == employee.company_id
#         ).first()
        
#         if not campaign:
#             raise ValidationError("Campaign not found")
        
#         # Get recipient count
#         recipient_count = self.db.query(CampaignRecipient).filter(
#             CampaignRecipient.campaign_id == campaign_id
#         ).count()
        
#         response_data = CampaignResponse.from_orm(campaign)
#         response_data.recipient_count = recipient_count
#         return response_data
    
#     def update_campaign(
#         self, 
#         campaign_id: int, 
#         campaign_data: CampaignUpdate, 
#         employee: Employee
#     ) -> CampaignResponse:
#         """Update campaign (only if draft)"""
#         campaign = self.db.query(Campaign).filter(
#             Campaign.id == campaign_id,
#             Campaign.company_id == employee.company_id
#         ).first()
        
#         if not campaign:
#             raise ValidationError("Campaign not found")
        
#         if campaign.status != "draft":
#             raise ValidationError("Can only update draft campaigns")
        
#         # Update fields
#         for field, value in campaign_data.dict(exclude_unset=True).items():
#             setattr(campaign, field, value)
        
#         self.db.commit()
#         self.db.refresh(campaign)
        
#         log_action(employee.id, "campaign_updated", f"Updated campaign: {campaign.title}")
        
#         # Get recipient count
#         recipient_count = self.db.query(CampaignRecipient).filter(
#             CampaignRecipient.campaign_id == campaign_id
#         ).count()
        
#         response_data = CampaignResponse.from_orm(campaign)
#         response_data.recipient_count = recipient_count
#         return response_data
    
#     def delete_campaign(self, campaign_id: int, employee: Employee) -> bool:
#         """Delete campaign (only if draft or failed)"""
#         campaign = self.db.query(Campaign).filter(
#             Campaign.id == campaign_id,
#             Campaign.company_id == employee.company_id
#         ).first()
        
#         if not campaign:
#             raise ValidationError("Campaign not found")
        
#         if campaign.status not in ["draft", "failed"]:
#             raise ValidationError("Can only delete draft or failed campaigns")
        
#         # Delete recipients first
#         self.db.query(CampaignRecipient).filter(
#             CampaignRecipient.campaign_id == campaign_id
#         ).delete()
        
#         self.db.delete(campaign)
#         self.db.commit()
        
#         log_action(employee.id, "campaign_deleted", f"Deleted campaign: {campaign.title}")
#         return True
    
#     def add_recipients(
#         self, 
#         campaign_id: int, 
#         recipients_data: CampaignAddRecipients, 
#         employee: Employee
#     ) -> dict:
#         """Add recipients to campaign"""
#         campaign = self.db.query(Campaign).filter(
#             Campaign.id == campaign_id,
#             Campaign.company_id == employee.company_id
#         ).first()
        
#         if not campaign:
#             raise ValidationError("Campaign not found")
        
#         if campaign.status != "draft":
#             raise ValidationError("Can only add recipients to draft campaigns")
        
#         added_count = 0
#         for customer_id in recipients_data.recipient_ids:
#             # Check if customer exists and belongs to company
#             customer = self.db.query(Customer).filter(
#                 Customer.id == customer_id,
#                 Customer.company_id == employee.company_id
#             ).first()
            
#             if not customer:
#                 continue
            
#             # Check if already added
#             existing = self.db.query(CampaignRecipient).filter(
#                 CampaignRecipient.campaign_id == campaign_id,
#                 CampaignRecipient.customer_id == customer_id
#             ).first()
            
#             if not existing:
#                 recipient = CampaignRecipient(
#                     campaign_id=campaign_id,
#                     customer_id=customer_id,
#                     status="pending"
#                 )
#                 self.db.add(recipient)
#                 added_count += 1
        
#         self.db.commit()
        
#         log_action(
#             employee.id, 
#             "recipients_added", 
#             f"Added {added_count} recipients to campaign: {campaign.title}"
#         )
        
#         return {"message": f"Added {added_count} recipients to campaign"}
    
#     async def send_campaign(
#         self, 
#         campaign_id: int, 
#         send_data: CampaignSend, 
#         employee: Employee
#     ) -> dict:
#         """Send campaign - if recipient_ids provided, use those; otherwise use all customers"""
#         campaign = self.db.query(Campaign).filter(
#             Campaign.id == campaign_id,
#             Campaign.company_id == employee.company_id
#         ).first()
        
#         if not campaign:
#             raise ValidationError("Campaign not found")
        
#         if campaign.status not in ["draft"]:
#             raise ValidationError("Campaign must be in draft status to send")
        
#         # If specific recipients provided, add them
#         if send_data.recipient_ids:
#             # Clear existing recipients and add new ones
#             self.db.query(CampaignRecipient).filter(
#                 CampaignRecipient.campaign_id == campaign_id
#             ).delete()
            
#             for customer_id in send_data.recipient_ids:
#                 # Verify customer belongs to company
#                 customer = self.db.query(Customer).filter(
#                     Customer.id == customer_id,
#                     Customer.company_id == employee.company_id
#                 ).first()
                
#                 if customer:
#                     recipient = CampaignRecipient(
#                         campaign_id=campaign_id,
#                         customer_id=customer_id,
#                         status="pending"
#                     )
#                     self.db.add(recipient)
            
#             self.db.commit()
        
#         # If no recipients specified and no existing recipients, add all customers
#         recipient_count = self.db.query(CampaignRecipient).filter(
#             CampaignRecipient.campaign_id == campaign_id
#         ).count()
        
#         if recipient_count == 0:
#             # Add all customers as recipients
#             all_customers = self.db.query(Customer).filter(
#                 Customer.company_id == employee.company_id
#             ).all()
            
#             for customer in all_customers:
#                 recipient = CampaignRecipient(
#                     campaign_id=campaign_id,
#                     customer_id=customer.id,
#                     status="pending"
#                 )
#                 self.db.add(recipient)
            
#             self.db.commit()
        
#         # Get recipients with customer details
#         recipients = self.db.query(CampaignRecipient, Customer).join(
#             Customer, CampaignRecipient.customer_id == Customer.id
#         ).filter(
#             CampaignRecipient.campaign_id == campaign_id,
#             CampaignRecipient.status == "pending"
#         ).all()
        
#         if not recipients:
#             raise ValidationError("No recipients found for campaign")
        
#         # Update campaign status
#         if send_data.schedule_at:
#             campaign.status = "scheduled"
#             campaign.scheduled_at = send_data.schedule_at
#             self.db.commit()
            
#             log_action(
#                 employee.id, 
#                 "campaign_scheduled", 
#                 f"Scheduled campaign {campaign.title} for {send_data.schedule_at}"
#             )
#             return {"message": "Campaign scheduled successfully"}
#         else:
#             campaign.status = "sending"
#             self.db.commit()
            
#             # Send emails immediately
#             return await self._send_emails(campaign, recipients, employee)
    
#     async def _send_emails(self, campaign: Campaign, recipients: List, employee: Employee) -> dict:
#         """Send emails to all recipients"""
#         try:
#             recipient_list = []
#             for recipient, customer in recipients:
#                 recipient_list.append({
#                     "email": customer.email,
#                     "recipient_id": recipient.id
#                 })
            
#             # Send bulk emails
#             results = await email_service.send_bulk_emails(
#                 recipients=recipient_list,
#                 subject=campaign.subject,
#                 body=campaign.body,  # This should be HTML content
#                 sender_email=campaign.sender_email,
#                 campaign_id=campaign.id
#             )
            
#             # Update campaign status
#             if results["failed"] == 0:
#                 campaign.status = "sent"
#             else:
#                 campaign.status = "partial"
            
#             campaign.sent_at = datetime.utcnow()
            
#             # Update recipient statuses
#             failed_emails = [error.split(":")[0] for error in results["errors"]]
#             for recipient, customer in recipients:
#                 if customer.email not in failed_emails:
#                     recipient.status = "sent"
#                     recipient.sent_at = datetime.utcnow()
#                 else:
#                     recipient.status = "failed"
            
#             self.db.commit()
            
#             log_action(
#                 employee.id, 
#                 "campaign_sent", 
#                 f"Campaign {campaign.title} sent to {results['sent']} recipients, {results['failed']} failed"
#             )
            
#             return {
#                 "message": "Campaign sent successfully",
#                 "sent_count": results["sent"],
#                 "failed_count": results["failed"],
#                 "errors": results["errors"]
#             }
            
#         except Exception as e:
#             campaign.status = "failed"
#             self.db.commit()
#             log_action(employee.id, "campaign_failed", f"Campaign {campaign.title} failed: {str(e)}")
#             raise EmailSendError(f"Failed to send campaign: {str(e)}")
    
#     def get_campaign_stats(self, campaign_id: int, employee: Employee) -> CampaignStats:
#         """Get campaign statistics"""
#         campaign = self.db.query(Campaign).filter(
#             Campaign.id == campaign_id,
#             Campaign.company_id == employee.company_id
#         ).first()
        
#         if not campaign:
#             raise ValidationError("Campaign not found")
        
#         # Get recipient counts
#         recipients = self.db.query(CampaignRecipient).filter(
#             CampaignRecipient.campaign_id == campaign_id
#         ).all()
        
#         total_recipients = len(recipients)
#         sent_count = len([r for r in recipients if r.status in ["sent", "opened", "clicked"]])
#         opened_count = len([r for r in recipients if r.opened_at is not None])
#         clicked_count = len([r for r in recipients if r.clicked_at is not None])
#         bounce_count = len([r for r in recipients if r.status == "bounced"])
        
#         open_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0
#         click_rate = (clicked_count / sent_count * 100) if sent_count > 0 else 0
        
#         return CampaignStats(
#             campaign_id=campaign_id,
#             total_recipients=total_recipients,
#             sent_count=sent_count,
#             opened_count=opened_count,
#             clicked_count=clicked_count,
#             bounce_count=bounce_count,
#             open_rate=round(open_rate, 2),
#             click_rate=round(click_rate, 2)
#         )



from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.exceptions import ValidationError, EmailSendError
from core.logger import log_action
from database.models import Campaign, CampaignRecipient, Customer, Employee
from utils.email_service import email_service
from .schemas import (
    CampaignCreate, 
    CampaignUpdate, 
    CampaignResponse, 
    CampaignSend,
    CampaignAddRecipients,
    CampaignStats,
    CampaignRecipientStatus
)

class CampaignService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(self, campaign_data: CampaignCreate, employee: Employee) -> CampaignResponse:
        """Create a new campaign (without recipients initially)"""
        campaign = Campaign(
            company_id=employee.company_id,
            created_by_employee_id=employee.id,
            status="draft",
            **campaign_data.dict()
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        log_action(employee.id, "campaign_created", f"Created campaign: {campaign.title}")
        
        # Get recipient count (0 initially)
        response_data = CampaignResponse.from_orm(campaign)
        response_data.recipient_count = 0
        return response_data
    
    def get_campaigns(self, employee: Employee, skip: int = 0, limit: int = 100) -> List[CampaignResponse]:
        """Get all campaigns with recipient counts"""
        campaigns_query = self.db.query(
            Campaign,
            func.count(CampaignRecipient.id).label('recipient_count')
        ).outerjoin(
            CampaignRecipient, Campaign.id == CampaignRecipient.campaign_id
        ).filter(
            Campaign.company_id == employee.company_id
        ).group_by(Campaign.id).offset(skip).limit(limit).all()
        
        result = []
        for campaign, recipient_count in campaigns_query:
            campaign_response = CampaignResponse.from_orm(campaign)
            campaign_response.recipient_count = recipient_count or 0
            result.append(campaign_response)
        
        return result
    
    def get_campaign(self, campaign_id: int, employee: Employee) -> CampaignResponse:
        """Get single campaign with recipient count"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        # Get recipient count
        recipient_count = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).count()
        
        response_data = CampaignResponse.from_orm(campaign)
        response_data.recipient_count = recipient_count
        return response_data
    
    def update_campaign(
        self, 
        campaign_id: int, 
        campaign_data: CampaignUpdate, 
        employee: Employee
    ) -> CampaignResponse:
        """Update campaign (only if draft)"""
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
        
        # Get recipient count
        recipient_count = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).count()
        
        response_data = CampaignResponse.from_orm(campaign)
        response_data.recipient_count = recipient_count
        return response_data
    
    def delete_campaign(self, campaign_id: int, employee: Employee) -> bool:
        """Delete campaign (only if draft or failed)"""
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
    
    def add_recipients(
        self, 
        campaign_id: int, 
        recipients_data: CampaignAddRecipients, 
        employee: Employee
    ) -> dict:
        """Add recipients to campaign"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        if campaign.status != "draft":
            raise ValidationError("Can only add recipients to draft campaigns")
        
        added_count = 0
        for customer_id in recipients_data.recipient_ids:
            # Check if customer exists and belongs to company
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id,
                Customer.company_id == employee.company_id
            ).first()
            
            if not customer:
                continue
            
            # Check if already added
            existing = self.db.query(CampaignRecipient).filter(
                CampaignRecipient.campaign_id == campaign_id,
                CampaignRecipient.customer_id == customer_id
            ).first()
            
            if not existing:
                recipient = CampaignRecipient(
                    campaign_id=campaign_id,
                    customer_id=customer_id,
                    status="pending"
                )
                self.db.add(recipient)
                added_count += 1
        
        self.db.commit()
        
        log_action(
            employee.id, 
            "recipients_added", 
            f"Added {added_count} recipients to campaign: {campaign.title}"
        )
        
        return {"message": f"Added {added_count} recipients to campaign"}
    
    async def send_campaign(
        self, 
        campaign_id: int, 
        send_data: CampaignSend, 
        employee: Employee
    ) -> dict:
        """Send campaign - if recipient_ids provided, use those; otherwise use all customers"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        if campaign.status not in ["draft"]:
            raise ValidationError("Campaign must be in draft status to send")
        
        # If specific recipients provided, add them
        if send_data.recipient_ids:
            # Clear existing recipients and add new ones
            self.db.query(CampaignRecipient).filter(
                CampaignRecipient.campaign_id == campaign_id
            ).delete()
            
            for customer_id in send_data.recipient_ids:
                # Verify customer belongs to company
                customer = self.db.query(Customer).filter(
                    Customer.id == customer_id,
                    Customer.company_id == employee.company_id
                ).first()
                
                if customer:
                    recipient = CampaignRecipient(
                        campaign_id=campaign_id,
                        customer_id=customer_id,
                        status="pending"
                    )
                    self.db.add(recipient)
            
            self.db.commit()
        
        # If no recipients specified and no existing recipients, add all customers
        recipient_count = self.db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).count()
        
        if recipient_count == 0:
            # Add all customers as recipients
            all_customers = self.db.query(Customer).filter(
                Customer.company_id == employee.company_id
            ).all()
            
            for customer in all_customers:
                recipient = CampaignRecipient(
                    campaign_id=campaign_id,
                    customer_id=customer.id,
                    status="pending"
                )
                self.db.add(recipient)
            
            self.db.commit()
        
        # Get recipients with customer details
        recipients = self.db.query(CampaignRecipient, Customer).join(
            Customer, CampaignRecipient.customer_id == Customer.id
        ).filter(
            CampaignRecipient.campaign_id == campaign_id,
            CampaignRecipient.status == "pending"
        ).all()
        
        if not recipients:
            raise ValidationError("No recipients found for campaign")
        
        # Update campaign status
        if send_data.schedule_at:
            campaign.status = "scheduled"
            campaign.scheduled_at = send_data.schedule_at
            self.db.commit()
            
            log_action(
                employee.id, 
                "campaign_scheduled", 
                f"Scheduled campaign {campaign.title} for {send_data.schedule_at}"
            )
            return {"message": "Campaign scheduled successfully"}
        else:
            campaign.status = "sending"
            self.db.commit()
            
            # Send emails immediately
            return await self._send_emails(campaign, recipients, employee)
    
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
                body=campaign.body,  # This should be HTML content
                sender_email=campaign.sender_email,
                campaign_id=campaign.id
            )
            
            # Update campaign status
            if results["failed"] == 0:
                campaign.status = "sent"
            else:
                campaign.status = "partial"
            
            campaign.sent_at = datetime.utcnow()
            
            # Update recipient statuses
            failed_emails = [error.split(":")[0] for error in results["errors"]]
            for recipient, customer in recipients:
                if customer.email not in failed_emails:
                    recipient.status = "sent"
                    recipient.sent_at = datetime.utcnow()
                else:
                    recipient.status = "failed"
            
            self.db.commit()
            
            log_action(
                employee.id, 
                "campaign_sent", 
                f"Campaign {campaign.title} sent to {results['sent']} recipients, {results['failed']} failed"
            )
            
            return {
                "message": "Campaign sent successfully",
                "sent_count": results["sent"],
                "failed_count": results["failed"],
                "errors": results["errors"]
            }
            
        except Exception as e:
            campaign.status = "failed"
            self.db.commit()
            log_action(employee.id, "campaign_failed", f"Campaign {campaign.title} failed: {str(e)}")
            raise EmailSendError(f"Failed to send campaign: {str(e)}")
    
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

    def get_campaign_recipients(self, campaign_id: int, employee: Employee) -> List[CampaignRecipientStatus]:
        """Get all recipients for a campaign with their status"""
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.company_id == employee.company_id
        ).first()
        
        if not campaign:
            raise ValidationError("Campaign not found")
        
        # Get recipients with customer details
        recipients_query = self.db.query(CampaignRecipient, Customer).join(
            Customer, CampaignRecipient.customer_id == Customer.id
        ).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).all()
        
        recipients_list = []
        for recipient, customer in recipients_query:
            recipient_status = CampaignRecipientStatus(
                recipient_id=recipient.id,
                customer_id=customer.id,
                customer_name=customer.name,
                customer_email=customer.email,
                status=recipient.status,
                sent_at=recipient.sent_at,
                opened_at=recipient.opened_at,
                clicked_at=recipient.clicked_at
            )
            recipients_list.append(recipient_status)
        
        return recipients_list

    def track_email_open(self, campaign_id: int, recipient_id: int) -> bool:
        """Track email open by updating recipient status"""
        try:
            recipient = self.db.query(CampaignRecipient).filter(
                CampaignRecipient.id == recipient_id,
                CampaignRecipient.campaign_id == campaign_id
            ).first()
            
            if recipient and recipient.opened_at is None:
                # Update status to opened and set opened_at timestamp
                recipient.status = "opened"
                recipient.opened_at = datetime.utcnow()
                self.db.commit()
                return True
                
        except Exception as e:
            # Silently fail for tracking - don't break email display
            pass
        
        return False