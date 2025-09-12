# from typing import List, Optional, Dict
# from sqlalchemy.orm import Session
# import uuid
# from datetime import datetime
# from core.exceptions import ValidationError
# from core.logger import log_action
# from database.models import WhatsAppTemplate, Employee
# from utils.whatsapp_service import whatsapp_service

# class WhatsAppTemplateService:
#     def __init__(self, db: Session):
#         self.db = db

#     def create_template(self, template_data: dict, employee: Employee) -> WhatsAppTemplate:
#         """Create a new WhatsApp template"""
#         # Check if template name already exists for this company
#         existing = self.db.query(WhatsAppTemplate).filter(
#             WhatsAppTemplate.company_id == employee.company_id,
#             WhatsAppTemplate.name == template_data['name']
#         ).first()
        
#         if existing:
#             raise ValidationError(f"Template with name '{template_data['name']}' already exists")
        
#         template = WhatsAppTemplate(
#             id=str(uuid.uuid4())[:8],
#             company_id=employee.company_id,
#             name=template_data['name'],
#             language=template_data.get('language', 'en_US'),
#             category=template_data.get('category', 'MARKETING'),
#             status='draft',
#             body=template_data['body'],
#             header=template_data.get('header'),
#             footer=template_data.get('footer'),
#             buttons=template_data.get('buttons'),
#             created_at=datetime.utcnow()
#         )
        
#         self.db.add(template)
#         self.db.commit()
#         self.db.refresh(template)
        
#         log_action(employee.id, "whatsapp_template_created", f"Created WhatsApp template: {template.name}")
#         return template

#     def get_templates(self, employee: Employee, status: Optional[str] = None) -> List[WhatsAppTemplate]:
#         """Get templates for company, optionally filter by status"""
#         query = self.db.query(WhatsAppTemplate).filter(
#             WhatsAppTemplate.company_id == employee.company_id
#         )
        
#         if status:
#             query = query.filter(WhatsAppTemplate.status == status)
        
#         return query.order_by(WhatsAppTemplate.created_at.desc()).all()

#     def get_template(self, template_id: str, employee: Employee) -> WhatsAppTemplate:
#         """Get single template"""
#         if not template_id or len(template_id) != 8:
#             raise ValidationError("Invalid template ID format")
        
#         template = self.db.query(WhatsAppTemplate).filter(
#             WhatsAppTemplate.id == template_id,
#             WhatsAppTemplate.company_id == employee.company_id
#         ).first()
        
#         if not template:
#             raise ValidationError("Template not found")
        
#         return template

#     def update_template(self, template_id: str, template_data: dict, employee: Employee) -> WhatsAppTemplate:
#         """Update template (only if draft or rejected)"""
#         template = self.get_template(template_id, employee)
        
#         if template.status not in ['draft', 'rejected']:
#             raise ValidationError("Can only update draft or rejected templates")
        
#         # Update fields
#         for field, value in template_data.items():
#             if hasattr(template, field) and value is not None:
#                 setattr(template, field, value)
        
#         template.status = 'draft'  # Reset to draft after changes
#         self.db.commit()
#         self.db.refresh(template)
        
#         log_action(employee.id, "whatsapp_template_updated", f"Updated WhatsApp template: {template.name}")
#         return template

#     def submit_to_meta(self, template_id: str, employee: Employee) -> Dict:
#         """Submit template to Meta for approval"""
#         template = self.get_template(template_id, employee)
        
#         if template.status != 'draft':
#             raise ValidationError("Only draft templates can be submitted for review")
        
#         # Prepare Meta API payload
#         components = []
        
#         if template.header:
#             components.append({
#                 "type": "HEADER",
#                 "format": "TEXT",
#                 "text": template.header
#             })
        
#         components.append({
#             "type": "BODY",
#             "text": template.body
#         })
        
#         if template.footer:
#             components.append({
#                 "type": "FOOTER", 
#                 "text": template.footer
#             })
        
#         if template.buttons:
#             components.append({
#                 "type": "BUTTONS",
#                 "buttons": template.buttons
#             })
        
#         meta_payload = {
#             "name": template.name,
#             "language": template.language,
#             "category": template.category,
#             "components": components
#         }
        
#         # Submit to Meta
#         result = whatsapp_service.submit_template_to_meta(meta_payload)
        
#         if result.get("success"):
#             template.status = 'submitted'
#             log_action(employee.id, "whatsapp_template_submitted", f"Submitted template {template.name} to Meta")
#         else:
#             template.status = 'rejected'
#             log_action(employee.id, "whatsapp_template_submission_failed", f"Failed to submit template {template.name}: {result.get('error')}")
        
#         self.db.commit()
#         self.db.refresh(template)
        
#         return {
#             "template_id": template.id,
#             "status": template.status,
#             "meta_response": result
#         }

#     def sync_meta_templates(self, employee: Employee) -> Dict:
#         """Sync approved templates from Meta"""
#         try:
#             meta_response = whatsapp_service.fetch_meta_templates()
            
#             if "error" in meta_response:
#                 return {"synced": 0, "errors": [meta_response["error"]]}
            
#             templates = meta_response.get("data", [])
#             synced_count = 0
#             errors = []
            
#             for meta_template in templates:
#                 try:
#                     name = meta_template.get("name")
#                     language = meta_template.get("language", "en_US")
#                     status = meta_template.get("status", "APPROVED").lower()
                    
#                     if status != "approved":
#                         continue
                    
#                     # Check if template already exists
#                     existing = self.db.query(WhatsAppTemplate).filter(
#                         WhatsAppTemplate.company_id == employee.company_id,
#                         WhatsAppTemplate.name == name,
#                         WhatsAppTemplate.language == language
#                     ).first()
                    
#                     if existing:
#                         # Update existing template
#                         existing.status = 'approved'
#                         existing.category = meta_template.get("category", "MARKETING")
#                         synced_count += 1
#                     else:
#                         # Create new template
#                         body = self._extract_body_from_components(meta_template.get("components", []))
#                         header = self._extract_header_from_components(meta_template.get("components", []))
#                         footer = self._extract_footer_from_components(meta_template.get("components", []))
#                         buttons = self._extract_buttons_from_components(meta_template.get("components", []))
                        
#                         new_template = WhatsAppTemplate(
#                             id=str(uuid.uuid4())[:8],
#                             company_id=employee.company_id,
#                             name=name,
#                             language=language,
#                             category=meta_template.get("category", "MARKETING"),
#                             status='approved',
#                             body=body,
#                             header=header,
#                             footer=footer,
#                             buttons=buttons,
#                             created_at=datetime.utcnow()
#                         )
#                         self.db.add(new_template)
#                         synced_count += 1
                
#                 except Exception as e:
#                     errors.append(f"Error syncing template {meta_template.get('name', 'unknown')}: {str(e)}")
            
#             self.db.commit()
            
#             log_action(employee.id, "whatsapp_templates_synced", f"Synced {synced_count} templates from Meta")
            
#             return {
#                 "synced": synced_count,
#                 "errors": errors,
#                 "total_meta_templates": len(templates)
#             }
            
#         except Exception as e:
#             return {"synced": 0, "errors": [f"Failed to sync templates: {str(e)}"]}

#     def _extract_body_from_components(self, components: List[Dict]) -> str:
#         """Extract body text from Meta template components"""
#         for component in components:
#             if component.get("type") == "BODY":
#                 return component.get("text", "")
#         return ""

#     def _extract_header_from_components(self, components: List[Dict]) -> Optional[str]:
#         """Extract header from Meta template components"""
#         for component in components:
#             if component.get("type") == "HEADER":
#                 return component.get("text")
#         return None

#     def _extract_footer_from_components(self, components: List[Dict]) -> Optional[str]:
#         """Extract footer from Meta template components"""
#         for component in components:
#             if component.get("type") == "FOOTER":
#                 return component.get("text")
#         return None

#     def _extract_buttons_from_components(self, components: List[Dict]) -> Optional[List[Dict]]:
#         """Extract buttons from Meta template components"""
#         for component in components:
#             if component.get("type") == "BUTTONS":
#                 return component.get("buttons", [])
#         return None




from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import uuid
import re
from datetime import datetime
from core.exceptions import ValidationError
from core.logger import log_action
from database.models import WhatsAppTemplate, Employee
from utils.whatsapp_service import whatsapp_service

class WhatsAppTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def create_template(self, template_data: dict, employee: Employee) -> WhatsAppTemplate:
        """Create a new WhatsApp template with media support"""
        # Check if template name already exists for this company
        existing = self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.company_id == employee.company_id,
            WhatsAppTemplate.name == template_data['name']
        ).first()
        
        if existing:
            raise ValidationError(f"Template with name '{template_data['name']}' already exists")
        
        # Count body parameters ({{1}}, {{2}}, etc.)
        body_text = template_data.get('body', '')
        parameter_count = len(re.findall(r'\{\{\d+\}\}', body_text))
        
        template = WhatsAppTemplate(
            id=str(uuid.uuid4())[:8],
            company_id=employee.company_id,
            name=template_data['name'],
            language=template_data.get('language', 'en_US'),
            category=template_data.get('category', 'MARKETING'),
            status='draft',
            body=body_text,
            header=template_data.get('header'),
            footer=template_data.get('footer'),
            buttons=template_data.get('buttons'),
            
            # NEW MEDIA FIELDS
            header_type=template_data.get('header_type', 'text'),
            header_media_url=template_data.get('header_media_url'),
            header_location_data=template_data.get('header_location_data'),
            body_parameters_count=parameter_count,
            
            created_at=datetime.utcnow()
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        log_action(employee.id, "whatsapp_template_created", f"Created WhatsApp template: {template.name}")
        return template

    def get_templates(self, employee: Employee, status: Optional[str] = None) -> List[WhatsAppTemplate]:
        """Get templates for company, optionally filter by status"""
        query = self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.company_id == employee.company_id
        )
        
        if status:
            query = query.filter(WhatsAppTemplate.status == status)
        
        return query.order_by(WhatsAppTemplate.created_at.desc()).all()

    def get_template(self, template_id: str, employee: Employee) -> WhatsAppTemplate:
        """Get single template"""
        if not template_id or len(template_id) != 8:
            raise ValidationError("Invalid template ID format")
        
        template = self.db.query(WhatsAppTemplate).filter(
            WhatsAppTemplate.id == template_id,
            WhatsAppTemplate.company_id == employee.company_id
        ).first()
        
        if not template:
            raise ValidationError("Template not found")
        
        return template

    def update_template(self, template_id: str, template_data: dict, employee: Employee) -> WhatsAppTemplate:
        """Update template (only if draft or rejected)"""
        template = self.get_template(template_id, employee)
        
        if template.status not in ['draft', 'rejected']:
            raise ValidationError("Can only update draft or rejected templates")
        
        # Update fields including new media fields
        for field, value in template_data.items():
            if hasattr(template, field) and value is not None:
                setattr(template, field, value)
        
        # Recalculate parameter count if body changed
        if 'body' in template_data:
            parameter_count = len(re.findall(r'\{\{\d+\}\}', template_data['body']))
            template.body_parameters_count = parameter_count
        
        template.status = 'draft'  # Reset to draft after changes
        self.db.commit()
        self.db.refresh(template)
        
        log_action(employee.id, "whatsapp_template_updated", f"Updated WhatsApp template: {template.name}")
        return template
    

    def delete_template(self, template_id: str, employee: Employee) -> Dict:
        """Delete template (only draft or rejected templates)"""
        template = self.get_template(template_id, employee)
        
        if template.status not in ['draft', 'rejected']:
            raise ValidationError("Can only delete draft or rejected templates")
        
        # Check if template is being used in any campaigns
        from database.models import Campaign
        campaigns_using_template = self.db.query(Campaign).filter(
            Campaign.template_name == template.name,
            Campaign.company_id == employee.company_id,
            Campaign.channel == "whatsapp"
        ).all()
        
        if campaigns_using_template:
            campaign_titles = [c.title for c in campaigns_using_template[:3]]  # Show max 3
            more_text = f" and {len(campaigns_using_template) - 3} more" if len(campaigns_using_template) > 3 else ""
            raise ValidationError(
                f"Cannot delete template. It's being used in campaigns: {', '.join(campaign_titles)}{more_text}"
            )
        
        template_name = template.name
        self.db.delete(template)
        self.db.commit()
        
        log_action(employee.id, "whatsapp_template_deleted", f"Deleted WhatsApp template: {template_name}")
        
        return {
            "message": "Template deleted successfully",
            "template_id": template_id,
            "template_name": template_name
        }

    def submit_to_meta(self, template_id: str, employee: Employee) -> Dict:
        """Submit template to Meta for approval with full media support"""
        template = self.get_template(template_id, employee)
        
        if template.status != 'draft':
            raise ValidationError("Only draft templates can be submitted for review")
        
        # Prepare Meta API payload with media support
        components = []
        
        # Handle different header types
        if template.header_type and template.header_type != "none":
            header_component = {"type": "HEADER"}
            
            if template.header_type == "text" and template.header:
                header_component["format"] = "TEXT"
                header_component["text"] = template.header
                
            elif template.header_type == "image":
                header_component["format"] = "IMAGE"
                if template.header_media_url:
                    header_component["example"] = {"header_url": [template.header_media_url]}
                    
            elif template.header_type == "video":
                header_component["format"] = "VIDEO"
                if template.header_media_url:
                    header_component["example"] = {"header_url": [template.header_media_url]}
                    
            elif template.header_type == "document":
                header_component["format"] = "DOCUMENT"
                if template.header_media_url:
                    header_component["example"] = {"header_url": [template.header_media_url]}
                    
            elif template.header_type == "location":
                header_component["format"] = "LOCATION"
                # Location headers don't need additional config in template submission
                
            if "format" in header_component:
                components.append(header_component)
        
        # Body component with parameters
        body_component = {"type": "BODY", "text": template.body}
        
        # Add parameter examples if body has parameters
        if template.body_parameters_count > 0:
            examples = []
            for i in range(1, template.body_parameters_count + 1):
                examples.append(f"Example {i}")
            body_component["example"] = {"body_text": [examples]}
        
        components.append(body_component)
        
        # Footer component
        if template.footer:
            components.append({
                "type": "FOOTER", 
                "text": template.footer
            })
        
        # Button components
        if template.buttons:
            button_component = {"type": "BUTTONS", "buttons": []}
            
            for button in template.buttons:
                button_config = {"type": button.get("type", "URL")}
                
                if button.get("type") == "URL":
                    button_config["text"] = button.get("text", "Visit Website")
                    button_config["url"] = button.get("url", "https://example.com/{{1}}")
                    
                    # Add URL parameter example
                    if "{{1}}" in button.get("url", ""):
                        button_config["example"] = ["https://example.com/"]
                        
                elif button.get("type") == "PHONE_NUMBER":
                    button_config["text"] = button.get("text", "Call Us")
                    button_config["phone_number"] = button.get("phone_number", "+1234567890")
                    
                elif button.get("type") == "QUICK_REPLY":
                    button_config["text"] = button.get("text", "Reply")
                
                button_component["buttons"].append(button_config)
            
            if button_component["buttons"]:
                components.append(button_component)
        
        # Final Meta payload
        meta_payload = {
            "name": template.name,
            "language": template.language,
            "category": template.category,
            "components": components
        }
        
        # Submit to Meta
        result = whatsapp_service.submit_template_to_meta(meta_payload)
        
        if result.get("success"):
            template.status = 'submitted'
            # Store Meta template ID if provided
            meta_response = result.get("response", {})
            if meta_response.get("id"):
                template.meta_template_id = meta_response["id"]
            
            log_action(employee.id, "whatsapp_template_submitted", f"Submitted template {template.name} to Meta")
        else:
            template.status = 'rejected'
            error_msg = result.get("error") or str(result.get("response", {}))
            template.rejection_reason = error_msg
            log_action(employee.id, "whatsapp_template_submission_failed", f"Failed to submit template {template.name}: {error_msg}")
        
        self.db.commit()
        self.db.refresh(template)
        
        return {
            "template_id": template.id,
            "status": template.status,
            "meta_response": result,
            "meta_payload": meta_payload  # Include payload for debugging
        }

    def sync_meta_templates(self, employee: Employee) -> Dict:
        """Sync approved templates from Meta with full media support"""
        try:
            meta_response = whatsapp_service.fetch_meta_templates()
            
            if "error" in meta_response:
                return {"synced": 0, "errors": [meta_response["error"]]}
            
            templates = meta_response.get("data", [])
            synced_count = 0
            errors = []
            
            for meta_template in templates:
                try:
                    name = meta_template.get("name")
                    language = meta_template.get("language", "en_US")
                    status = meta_template.get("status", "APPROVED").lower()
                    
                    if status != "approved":
                        continue
                    
                    # Check if template already exists
                    existing = self.db.query(WhatsAppTemplate).filter(
                        WhatsAppTemplate.company_id == employee.company_id,
                        WhatsAppTemplate.name == name,
                        WhatsAppTemplate.language == language
                    ).first()
                    
                    # Extract components with full media support
                    components = meta_template.get("components", [])
                    template_data = self._extract_template_data_from_components(components)
                    
                    if existing:
                        # Update existing template with new data
                        existing.status = 'approved'
                        existing.category = meta_template.get("category", "MARKETING")
                        existing.meta_template_id = meta_template.get("id")
                        existing.body = template_data["body"]
                        existing.header = template_data["header"]
                        existing.footer = template_data["footer"]
                        existing.buttons = template_data["buttons"]
                        existing.header_type = template_data["header_type"]
                        existing.body_parameters_count = template_data["parameter_count"]
                        synced_count += 1
                    else:
                        # Create new template
                        new_template = WhatsAppTemplate(
                            id=str(uuid.uuid4())[:8],
                            company_id=employee.company_id,
                            name=name,
                            language=language,
                            category=meta_template.get("category", "MARKETING"),
                            status='approved',
                            meta_template_id=meta_template.get("id"),
                            body=template_data["body"],
                            header=template_data["header"],
                            footer=template_data["footer"],
                            buttons=template_data["buttons"],
                            header_type=template_data["header_type"],
                            body_parameters_count=template_data["parameter_count"],
                            created_at=datetime.utcnow()
                        )
                        self.db.add(new_template)
                        synced_count += 1
                
                except Exception as e:
                    errors.append(f"Error syncing template {meta_template.get('name', 'unknown')}: {str(e)}")
            
            self.db.commit()
            
            log_action(employee.id, "whatsapp_templates_synced", f"Synced {synced_count} templates from Meta")
            
            return {
                "synced": synced_count,
                "errors": errors,
                "total_meta_templates": len(templates)
            }
            
        except Exception as e:
            return {"synced": 0, "errors": [f"Failed to sync templates: {str(e)}"]}

    def _extract_template_data_from_components(self, components: List[Dict]) -> Dict:
        """Extract template data from Meta components with full media support"""
        body = ""
        header = None
        footer = None
        buttons = None
        header_type = "text"
        parameter_count = 0
        
        for component in components:
            comp_type = component.get("type", "").upper()
            
            if comp_type == "BODY":
                body = component.get("text", "")
                parameter_count = len(re.findall(r'\{\{\d+\}\}', body))
                
            elif comp_type == "HEADER":
                format_type = component.get("format", "TEXT").lower()
                
                if format_type == "text":
                    header = component.get("text")
                    header_type = "text"
                elif format_type == "image":
                    header_type = "image"
                elif format_type == "video":
                    header_type = "video"
                elif format_type == "document":
                    header_type = "document"
                elif format_type == "location":
                    header_type = "location"
                    
            elif comp_type == "FOOTER":
                footer = component.get("text")
                
            elif comp_type == "BUTTONS":
                buttons = component.get("buttons", [])
        
        return {
            "body": body,
            "header": header,
            "footer": footer,
            "buttons": buttons,
            "header_type": header_type,
            "parameter_count": parameter_count
        }

    def upload_media_for_template(self, file_path: str, media_type: str, employee: Employee) -> Dict:
        """Upload media file and return media ID for template use"""
        try:
            media_id = whatsapp_service.upload_media(file_path, media_type)
            
            log_action(
                employee.id, 
                "whatsapp_media_uploaded", 
                f"Uploaded media file {file_path} with ID {media_id}"
            )
            
            return {
                "media_id": media_id,
                "success": True,
                "file_path": file_path,
                "media_type": media_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }