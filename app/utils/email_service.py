
# ### utils/email_service.py
# import smtplib
# import asyncio
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from typing import List
# from core.config import settings
# from core.exceptions import EmailSendError
# from core.logger import logger

# class EmailService:
#     def __init__(self):
#         self.smtp_host = settings.SMTP_HOST
#         self.smtp_port = settings.SMTP_PORT
#         self.smtp_user = settings.SMTP_USER
#         self.smtp_password = settings.SMTP_PASSWORD
    
#     async def send_email(
#         self,
#         to_email: str,
#         subject: str,
#         body: str,
#         sender_email: str,
#         campaign_id: int = None,
#         recipient_id: int = None
#     ) -> bool:
#         """Send email with tracking pixels"""
#         try:
#             # Add tracking pixel to body
#             tracking_pixel = f'<img src="http://localhost:8000/api/tracking/open/{campaign_id}/{recipient_id}" width="1" height="1" style="display:none;">'
#             body_with_tracking = body + tracking_pixel
            
#             # Create message
#             msg = MimeMultipart()
#             msg['From'] = sender_email
#             msg['To'] = to_email
#             msg['Subject'] = subject
#             msg.attach(MimeText(body_with_tracking, 'html'))
            
#             # Simulate email sending (replace with actual SMTP in production)
#             await asyncio.sleep(0.1)  # Simulate network delay
#             logger.info(f"Email sent successfully to {to_email}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Failed to send email to {to_email}: {str(e)}")
#             raise EmailSendError(f"Failed to send email: {str(e)}")
    
#     async def send_bulk_emails(
#         self,
#         recipients: List[dict],
#         subject: str,
#         body: str,
#         sender_email: str,
#         campaign_id: int
#     ) -> dict:
#         """Send emails to multiple recipients"""
#         results = {"sent": 0, "failed": 0, "errors": []}
        
#         for recipient in recipients:
#             try:
#                 success = await self.send_email(
#                     to_email=recipient["email"],
#                     subject=subject,
#                     body=body,
#                     sender_email=sender_email,
#                     campaign_id=campaign_id,
#                     recipient_id=recipient["recipient_id"]
#                 )
#                 if success:
#                     results["sent"] += 1
#             except Exception as e:
#                 results["failed"] += 1
#                 results["errors"].append(f"{recipient['email']}: {str(e)}")
        
#         return results

# email_service = EmailService()



### utils/email_service.py
import os
import ssl
import smtplib
import asyncio
import socket
from email.message import EmailMessage
from typing import List
from core.exceptions import EmailSendError
from core.logger import logger

class EmailService:
    def __init__(self):
        # Hardcoded Gmail credentials for testing
        self.EMAIL_USER = 'pinesphere6@gmail.com'
        self.EMAIL_PASS = 'wfei aajr xeld gcej'
        
        # Try multiple SMTP configurations
        self.smtp_configs = [
            {"host": "smtp.gmail.com", "port": 587, "use_tls": True},  # TLS
            {"host": "smtp.gmail.com", "port": 465, "use_ssl": True},  # SSL
            {"host": "smtp.gmail.com", "port": 25, "use_tls": True},   # Alternative
        ]
    
    async def _test_smtp_connection(self, config):
        """Test SMTP connection with given configuration"""
        try:
            if config.get("use_ssl"):
                server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=10)
            else:
                server = smtplib.SMTP(config["host"], config["port"], timeout=10)
                if config.get("use_tls"):
                    server.starttls()
            
            server.login(self.EMAIL_USER, self.EMAIL_PASS)
            server.quit()
            return True
        except Exception as e:
            logger.warning(f"SMTP config {config} failed: {str(e)}")
            return False
    
    async def _get_working_smtp_config(self):
        """Find a working SMTP configuration"""
        for config in self.smtp_configs:
            if await self._test_smtp_connection(config):
                return config
        return None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_email: str,
        campaign_id: int = None,
        recipient_id: int = None
    ) -> bool:
        """Send email with tracking pixels using Gmail SMTP"""
        try:
            # Test DNS resolution first
            try:
                socket.gethostbyname('smtp.gmail.com')
            except socket.gaierror as e:
                logger.error(f"DNS resolution failed for smtp.gmail.com: {str(e)}")
                raise EmailSendError(f"DNS resolution failed: {str(e)}")
            
            # Get working SMTP configuration
            smtp_config = await self._get_working_smtp_config()
            if not smtp_config:
                raise EmailSendError("No working SMTP configuration found")
            
            # Create email message
            msg = EmailMessage()
            msg["From"] = self.EMAIL_USER  # Use the Gmail account as sender
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Add tracking pixel to HTML body if campaign tracking is needed
            tracking_pixel = ""
            if campaign_id and recipient_id:
                tracking_pixel = f'<img src="https://5c7nhw22-8000.inc1.devtunnels.ms/api/campaigns/tracking/open/{campaign_id}/{recipient_id}" width="1" height="1" style="display:none;">'
            
            # Create HTML version with tracking
            html_body = f"""
            <!doctype html>
            <html>
                <body style="font-family: system-ui, -apple-system, sans-serif;">
                    {body}
                    {tracking_pixel}
                </body>
            </html>
            """
            
            # Set plain text content (fallback)
            # Strip HTML tags for plain text version
            import re
            plain_text = re.sub('<[^<]+?>', '', body)
            msg.set_content(plain_text)
            
            # Add HTML version
            msg.add_alternative(html_body, subtype="html")
            
            # Send email using the working SMTP configuration
            if smtp_config.get("use_ssl"):
                with smtplib.SMTP_SSL(
                    smtp_config["host"], 
                    smtp_config["port"], 
                    context=ssl.create_default_context(),
                    timeout=30
                ) as server:
                    server.login(self.EMAIL_USER, self.EMAIL_PASS)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=30) as server:
                    if smtp_config.get("use_tls"):
                        server.starttls(context=ssl.create_default_context())
                    server.login(self.EMAIL_USER, self.EMAIL_PASS)
                    server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email} using {smtp_config['host']}:{smtp_config['port']}")
            return True
            
        except socket.gaierror as e:
            error_msg = f"DNS resolution failed: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise EmailSendError(error_msg)
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise EmailSendError(error_msg)
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipient refused: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise EmailSendError(error_msg)
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"SMTP server disconnected: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise EmailSendError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise EmailSendError(error_msg)
    
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
        
        # Test connectivity first
        try:
            working_config = await self._get_working_smtp_config()
            if not working_config:
                logger.error("No working SMTP configuration available")
                results["errors"].append("SMTP service unavailable")
                results["failed"] = len(recipients)
                return results
        except Exception as e:
            logger.error(f"SMTP connectivity test failed: {str(e)}")
            results["errors"].append(f"SMTP connectivity failed: {str(e)}")
            results["failed"] = len(recipients)
            return results
        
        # Add small delay between emails to avoid rate limiting
        for i, recipient in enumerate(recipients):
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
                
                # Add delay between emails (Gmail has rate limits)
                if i < len(recipients) - 1:  # Don't delay after the last email
                    await asyncio.sleep(2)  # Increased to 2 seconds delay
                    
            except Exception as e:
                results["failed"] += 1
                error_msg = f"{recipient['email']}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(f"Failed to send to {recipient['email']}: {str(e)}")
                
                # Continue with next email even if one fails
                continue
        
        return results
    
    async def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration"""
        try:
            return await self.send_email(
                to_email=to_email,
                subject="Test Email from Campaign System",
                body="<h2>Test Email</h2><p>This is a test email from your campaign system. If you receive this, the email configuration is working correctly!</p>",
                sender_email=self.EMAIL_USER
            )
        except Exception as e:
            logger.error(f"Test email failed: {str(e)}")
            return False
    
    async def diagnose_connection(self) -> dict:
        """Diagnose email service connectivity"""
        diagnosis = {
            "dns_resolution": False,
            "working_configs": [],
            "failed_configs": [],
            "recommendations": []
        }
        
        # Test DNS resolution
        try:
            socket.gethostbyname('smtp.gmail.com')
            diagnosis["dns_resolution"] = True
        except Exception as e:
            diagnosis["recommendations"].append(f"DNS resolution failed: {str(e)}")
        
        # Test each SMTP configuration
        for config in self.smtp_configs:
            try:
                if await self._test_smtp_connection(config):
                    diagnosis["working_configs"].append(config)
                else:
                    diagnosis["failed_configs"].append(config)
            except Exception as e:
                diagnosis["failed_configs"].append({**config, "error": str(e)})
        
        # Add recommendations
        if not diagnosis["dns_resolution"]:
            diagnosis["recommendations"].append("Check internet connectivity and DNS settings")
        
        if not diagnosis["working_configs"]:
            diagnosis["recommendations"].extend([
                "Verify Gmail credentials are correct",
                "Check if 2-factor authentication is enabled (use app password)",
                "Verify firewall allows SMTP ports (25, 587, 465)",
                "Try different network connection"
            ])
        
        return diagnosis

# Global instance
email_service = EmailService()