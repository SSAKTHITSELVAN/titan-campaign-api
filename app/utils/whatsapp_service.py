import os
import requests
from typing import List, Dict, Optional
import json

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

class WhatsAppService:
    def __init__(self):
        self.api_base = GRAPH_API_BASE

    def _check_credentials(self):
        phone_number_id = os.getenv("WHATSAPP_TEST_PHONE_NUMBER_ID")
        access_token = os.getenv("WHATSAPP_PERMANENT_TOKEN")
        if not phone_number_id or not access_token:
            raise ValueError("WhatsApp API credentials not configured in .env")
        return phone_number_id, access_token

    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload media file to WhatsApp and return media ID"""
        phone_number_id, access_token = self._check_credentials()
        url = f"{self.api_base}/{phone_number_id}/media"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with open(file_path, 'rb') as media_file:
            files = {
                'file': (os.path.basename(file_path), media_file, media_type),
                'messaging_product': (None, 'whatsapp'),
                'type': (None, media_type.split('/')[0])  # image, video, document, audio
            }
            
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                return response.json().get('id')
            else:
                raise Exception(f"Media upload failed: {response.text}")

    def send_template_message(
        self,
        recipient_number: str,
        template_name: str = "hello_world",
        language_code: str = "en_US",
        components: List[Dict] = None,
        header_type: str = "text",
        header_content: str = None,
        header_media_id: str = None,
        header_media_url: str = None,
        body_parameters: List[str] = None,
        button_parameters: List[Dict] = None
    ) -> dict:
        """Send WhatsApp template message with full media support"""
        phone_number_id, access_token = self._check_credentials()
        url = f"{self.api_base}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Ensure phone number is in E.164 format
        if not recipient_number.startswith('+'):
            recipient_number = f"+{recipient_number}"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        # Build components if not provided
        if not components:
            template_components = []
            
            # Handle different header types
            if header_type and header_type.lower() != "none":
                header_component = {"type": "header"}
                
                if header_type.lower() == "text" and header_content:
                    header_component["parameters"] = [{"type": "text", "text": header_content}]
                
                elif header_type.lower() == "image":
                    if header_media_id:
                        header_component["parameters"] = [{"type": "image", "image": {"id": header_media_id}}]
                    elif header_media_url:
                        header_component["parameters"] = [{"type": "image", "image": {"link": header_media_url}}]
                
                elif header_type.lower() == "video":
                    if header_media_id:
                        header_component["parameters"] = [{"type": "video", "video": {"id": header_media_id}}]
                    elif header_media_url:
                        header_component["parameters"] = [{"type": "video", "video": {"link": header_media_url}}]
                
                elif header_type.lower() == "document":
                    if header_media_id:
                        header_component["parameters"] = [{"type": "document", "document": {"id": header_media_id}}]
                    elif header_media_url:
                        header_component["parameters"] = [{"type": "document", "document": {"link": header_media_url}}]
                
                elif header_type.lower() == "location":
                    # Location header requires latitude, longitude
                    if isinstance(header_content, dict) and "latitude" in header_content:
                        header_component["parameters"] = [{
                            "type": "location",
                            "location": {
                                "latitude": header_content["latitude"],
                                "longitude": header_content["longitude"],
                                "name": header_content.get("name", ""),
                                "address": header_content.get("address", "")
                            }
                        }]
                
                if "parameters" in header_component:
                    template_components.append(header_component)
            
            # Handle body parameters
            if body_parameters:
                body_component = {
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in body_parameters]
                }
                template_components.append(body_component)
            
            # Handle button parameters
            if button_parameters:
                for button_param in button_parameters:
                    button_component = {
                        "type": "button",
                        "sub_type": button_param.get("sub_type", "url"),
                        "index": button_param.get("index", 0),
                        "parameters": button_param.get("parameters", [])
                    }
                    template_components.append(button_component)
            
            if template_components:
                payload["template"]["components"] = template_components
        else:
            payload["template"]["components"] = components

        try:
            resp = requests.post(url, headers=headers, json=payload)
            return {
                "status_code": resp.status_code,
                "response": resp.json(),
                "success": resp.status_code == 200
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def send_bulk_template(
        self,
        recipients: List[str],
        template_name: str,
        language_code: str = "en_US",
        components: List[Dict] = None,
        **template_params
    ) -> dict:
        """Send template to multiple recipients"""
        results = {"sent": 0, "failed": 0, "errors": [], "details": []}
        
        for phone in recipients:
            try:
                resp = self.send_template_message(
                    phone, 
                    template_name, 
                    language_code, 
                    components,
                    **template_params
                )
                if resp.get("success"):
                    results["sent"] += 1
                    message_id = None
                    if resp.get("response", {}).get("messages"):
                        message_id = resp["response"]["messages"][0].get("id")
                    results["details"].append({
                        "phone": phone, 
                        "status": "sent", 
                        "message_id": message_id
                    })
                else:
                    results["failed"] += 1
                    error_msg = resp.get("error") or str(resp.get("response", {}))
                    results["errors"].append(f"{phone}: {error_msg}")
                    results["details"].append({
                        "phone": phone, 
                        "status": "failed", 
                        "error": error_msg
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{phone}: {str(e)}")
                results["details"].append({
                    "phone": phone, 
                    "status": "failed", 
                    "error": str(e)
                })
        
        return results

    def fetch_meta_templates(self) -> dict:
        """Fetch approved templates from Meta Business Account"""
        access_token = os.getenv("WHATSAPP_PERMANENT_TOKEN")
        business_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        if not access_token or not business_id:
            raise ValueError("WhatsApp Business credentials not configured")
        
        url = f"{self.api_base}/{business_id}/message_templates"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            resp = requests.get(url, headers=headers)
            return resp.json()
        except Exception as e:
            return {"error": str(e), "data": []}

    def submit_template_to_meta(self, template_data: dict) -> dict:
        """Submit template to Meta for approval"""
        access_token = os.getenv("WHATSAPP_PERMANENT_TOKEN")
        business_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        if not access_token or not business_id:
            raise ValueError("WhatsApp Business credentials not configured")
        
        url = f"{self.api_base}/{business_id}/message_templates"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            resp = requests.post(url, headers=headers, json=template_data)
            return {
                "status_code": resp.status_code,
                "response": resp.json(),
                "success": resp.status_code in [200, 201]
            }
        except Exception as e:
            return {"error": str(e), "success": False}

whatsapp_service = WhatsAppService()