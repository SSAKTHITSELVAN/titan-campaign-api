### modules/campaigns/controllers.py
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Employee
from utils.security import get_current_employee, require_role
from .services import CampaignService
from .schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignSend,
    CampaignStats
)

campaigns_router = APIRouter()

@campaigns_router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CampaignService(db)
    return service.create_campaign(campaign_data, current_employee)

@campaigns_router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = CampaignService(db)
    return service.get_campaigns(current_employee, skip, limit)

@campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = CampaignService(db)
    return service.get_campaign(campaign_id, current_employee)

@campaigns_router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CampaignService(db)
    return service.update_campaign(campaign_id, campaign_data, current_employee)

@campaigns_router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CampaignService(db)
    service.delete_campaign(campaign_id, current_employee)
    return {"message": "Campaign deleted successfully"}

@campaigns_router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    send_data: CampaignSend,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CampaignService(db)
    result = await service.send_campaign(campaign_id, send_data, current_employee)
    return result

@campaigns_router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = CampaignService(db)
    return service.get_campaign_stats(campaign_id, current_employee)
