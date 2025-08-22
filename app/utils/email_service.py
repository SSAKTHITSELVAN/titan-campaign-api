
### utils/email_service.py
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from core.config import settings
from core.exceptions import EmailSendError
from core.logger import logger

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_email: str,
        campaign_id: int = None,
        recipient_id: int = None
    ) -> bool:
        """Send email with tracking pixels"""
        try:
            # Add tracking pixel to body
            tracking_pixel = f'<img src="http://localhost:8000/api/tracking/open/{campaign_id}/{recipient_id}" width="1" height="1" style="display:none;">'
            body_with_tracking = body + tracking_pixel
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MimeText(body_with_tracking, 'html'))
            
            # Simulate email sending (replace with actual SMTP in production)
            await asyncio.sleep(0.1)  # Simulate network delay
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise EmailSendError(f"Failed to send email: {str(e)}")
    
    async def send_bulk_emails(
        self,
        recipients: List[dict],
        subject: str,
        body: str,
        sender_email: str,
        campaign_id: int
    ) -> dict:
        """Send emails to multiple recipients"""
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for recipient in recipients:
            try:
                success = await self.send_email(
                    to_email=recipient["email"],
                    subject=subject,
                    body=body,
                    sender_email=sender_email,
                    campaign_id=campaign_id,
                    recipient_id=recipient["recipient_id"]
                )
                if success:
                    results["sent"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{recipient['email']}: {str(e)}")
        
        return results

email_service = EmailService()
