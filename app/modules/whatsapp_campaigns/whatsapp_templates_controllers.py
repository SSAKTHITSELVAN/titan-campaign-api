from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models import Employee
from utils.security import require_role, get_current_employee
from .whatsapp_templates_service import WhatsAppTemplateService
from .whatsapp_schemas import WhatsAppTemplateCreate, WhatsAppTemplateResponse

whatsapp_templates_router = APIRouter()

@whatsapp_templates_router.post("/", response_model=WhatsAppTemplateResponse)
def create_template(
    template_data: WhatsAppTemplateCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Create a new WhatsApp template"""
    service = WhatsAppTemplateService(db)
    template = service.create_template(template_data.dict(), current_employee)
    return template

@whatsapp_templates_router.get("/", response_model=List[WhatsAppTemplateResponse])
def get_templates(
    status: Optional[str] = Query(None, description="Filter by status: draft, submitted, approved, rejected"),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all templates for company"""
    service = WhatsAppTemplateService(db)
    templates = service.get_templates(current_employee, status)
    return templates

@whatsapp_templates_router.get("/approved", response_model=List[WhatsAppTemplateResponse])
def get_approved_templates(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get only approved templates for creating campaigns"""
    service = WhatsAppTemplateService(db)
    templates = service.get_templates(current_employee, "approved")
    return templates

@whatsapp_templates_router.get("/{template_id}", response_model=WhatsAppTemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get single template"""
    service = WhatsAppTemplateService(db)
    template = service.get_template(template_id, current_employee)
    return template

@whatsapp_templates_router.put("/{template_id}", response_model=WhatsAppTemplateResponse)
def update_template(
    template_id: str,
    template_data: WhatsAppTemplateCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Update template (only draft or rejected)"""
    service = WhatsAppTemplateService(db)
    template = service.update_template(template_id, template_data.dict(), current_employee)
    return template

@whatsapp_templates_router.post("/{template_id}/submit")
def submit_template_to_meta(
    template_id: str,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Submit template to Meta for approval"""
    service = WhatsAppTemplateService(db)
    result = service.submit_to_meta(template_id, current_employee)
    return result

@whatsapp_templates_router.post("/sync-meta")
def sync_meta_templates(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Sync approved templates from Meta Business Account"""
    service = WhatsAppTemplateService(db)
    result = service.sync_meta_templates(current_employee)
    return result

@whatsapp_templates_router.put("/{template_id}/fix-media")
def fix_template_media(
    template_id: str,
    media_url: Optional[str] = None,
    new_header_type: str = "text",
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    """Fix template media configuration"""
    service = WhatsAppTemplateService(db)
    template = service.get_template(template_id, current_employee)
    
    if new_header_type in ["image", "video", "document"] and not media_url:
        raise HTTPException(400, "Media URL required for media header types")
    
    # Update template
    if new_header_type == "text":
        template.header_type = "text"
        template.header_media_url = None
        template.header_media_id = None
    else:
        template.header_type = new_header_type
        template.header_media_url = media_url
    
    db.commit()
    db.refresh(template)
    
    return {
        "message": "Template media configuration updated",
        "template_id": template.id,
        "header_type": template.header_type,
        "header_media_url": template.header_media_url
    }

# Also add a debug endpoint to check all templates
@whatsapp_templates_router.get("/debug/media-check")
def check_template_media(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Check all templates for media configuration issues"""
    service = WhatsAppTemplateService(db)
    templates = service.get_templates(current_employee)
    
    issues = []
    for template in templates:
        if template.header_type in ["image", "video", "document"]:
            if not template.header_media_url and not template.header_media_id:
                issues.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "issue": f"Expects {template.header_type.upper()} header but no media configured",
                    "header_type": template.header_type,
                    "status": template.status
                })
    
    return {
        "total_templates": len(templates),
        "media_issues": len(issues),
        "issues": issues
    }