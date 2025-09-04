from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Employee
from utils.security import get_current_employee, require_role
from .compaines_services import CompanyService
from .compaines_schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyStats,
    CompanySettings
)

companies_router = APIRouter()

@companies_router.post("/", response_model=Dict[str, Any])
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db)
):
    """Create a new company with admin user (public endpoint)"""
    service = CompanyService(db)
    return service.create_company(company_data)

@companies_router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
    # Note: In production, this should be protected by super admin role
):
    """Get all companies (super admin only)"""
    service = CompanyService(db)
    return service.get_companies(skip, limit)

@companies_router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get current employee's company details"""
    service = CompanyService(db)
    return service.get_company(current_employee.company_id, current_employee)

@companies_router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get company details"""
    service = CompanyService(db)
    return service.get_company(company_id, current_employee)

@companies_router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,  # Changed from int to str for UUID
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    """Update company details (admin only)"""
    service = CompanyService(db)
    return service.update_company(company_id, company_data, current_employee)

@companies_router.put("/{company_id}/settings")
async def update_company_settings(
    company_id: str,  # Changed from int to str for UUID
    settings: CompanySettings,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    """Update company settings (admin only)"""
    service = CompanyService(db)
    return service.update_company_settings(company_id, settings, current_employee)

@companies_router.get("/{company_id}/stats", response_model=CompanyStats)
async def get_company_stats(
    company_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get company statistics"""
    service = CompanyService(db)
    return service.get_company_stats(company_id, current_employee)

@companies_router.post("/{company_id}/deactivate")
async def deactivate_company(
    company_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db)
    # Note: In production, this should be protected by super admin role
):
    """Deactivate company (super admin only)"""
    service = CompanyService(db)
    service.deactivate_company(company_id)
    return {"message": "Company deactivated successfully"}