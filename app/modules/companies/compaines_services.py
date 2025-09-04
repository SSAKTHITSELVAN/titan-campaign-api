from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from core.exceptions import ValidationError
from core.logger import log_action
from database.models import Company, Employee, Customer, Campaign
from utils.security import get_password_hash
from .compaines_schemas import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanyResponse, 
    CompanyStats,
    CompanySettings
)

class CompanyService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_company(self, company_data: CompanyCreate) -> Dict[str, Any]:
        """Create a new company with admin user"""
        # Check if domain already exists
        existing_company = self.db.query(Company).filter(
            Company.domain == company_data.domain
        ).first()
        
        if existing_company:
            raise ValidationError(f"Company with domain {company_data.domain} already exists")
        
        # Check if admin email already exists
        existing_employee = self.db.query(Employee).filter(
            Employee.email == company_data.admin_email
        ).first()
        
        if existing_employee:
            raise ValidationError(f"Employee with email {company_data.admin_email} already exists")
        
        try:
            # Create company with UUID
            company = Company(
                id=str(uuid.uuid4())[:8],  # Generate UUID for company
                company_name=company_data.company_name,
                name=company_data.company_name,  # For backward compatibility
                domain=company_data.domain,
                industry=company_data.industry,
                company_size=company_data.company_size,
                website=company_data.website,
                phone=company_data.phone,
                country=company_data.country,
                timezone=company_data.timezone,
                business_type=company_data.business_type,
                description=company_data.description,
                primary_use_case=company_data.primary_use_case,
                expected_monthly_emails=company_data.expected_monthly_emails,
                settings={
                    "sender_name": company_data.company_name,
                    "timezone": company_data.timezone,
                    "email_verification_required": True,
                    "tracking_enabled": True
                }
            )
            
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
            
            # Create admin employee with UUID
            admin_employee = Employee(
                id=str(uuid.uuid4())[:8],  # Generate UUID for employee
                company_id=company.id,
                name=company_data.admin_name,
                email=company_data.admin_email,
                password_hash=get_password_hash(company_data.admin_password),
                role="admin"
            )
            
            self.db.add(admin_employee)
            self.db.commit()
            self.db.refresh(admin_employee)
            
            log_action(
                admin_employee.id,
                "company_created",
                f"Created company {company.company_name} with admin {admin_employee.name}"
            )
            
            return {
                "company": self._format_company_response(company),
                "admin_employee": {
                    "id": admin_employee.id,
                    "name": admin_employee.name,
                    "email": admin_employee.email,
                    "role": admin_employee.role
                },
                "message": "Company created successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create company: {str(e)}")
    
    def get_company(self, company_id: str, current_employee: Employee = None) -> CompanyResponse:
        """Get company details by UUID"""
        # Validate UUID format
        if not company_id or len(company_id) != 8:
            raise ValidationError("Invalid company ID format")
        
        query = self.db.query(Company).filter(Company.id == company_id)
        
        # If called from employee context, ensure they belong to the company
        if current_employee and current_employee.company_id != company_id:
            raise ValidationError("Access denied")
        
        company = query.first()
        if not company:
            raise ValidationError("Company not found")
        
        return self._format_company_response(company)
    
    def get_companies(self, skip: int = 0, limit: int = 100) -> List[CompanyResponse]:
        """Get all companies (super admin only)"""
        companies = self.db.query(Company).offset(skip).limit(limit).all()
        return [self._format_company_response(company) for company in companies]
    
    def update_company(
        self, 
        company_id: str, 
        company_data: CompanyUpdate, 
        current_employee: Employee
    ) -> CompanyResponse:
        """Update company details"""
        # Validate UUID format
        if not company_id or len(company_id) != 8:
            raise ValidationError("Invalid company ID format")
        
        if current_employee.company_id != company_id:
            raise ValidationError("Access denied")
        
        if current_employee.role != "admin":
            raise ValidationError("Only admin can update company details")
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValidationError("Company not found")
        
        # Update fields
        update_data = company_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(company, field):
                setattr(company, field, value)
        
        # Update name field for backward compatibility
        if 'company_name' in update_data:
            company.name = update_data['company_name']
        
        self.db.commit()
        self.db.refresh(company)
        
        log_action(
            current_employee.id,
            "company_updated",
            f"Updated company {company.company_name}"
        )
        
        return self._format_company_response(company)
    
    def update_company_settings(
        self,
        company_id: str,
        settings: CompanySettings,
        current_employee: Employee
    ) -> Dict[str, Any]:
        """Update company settings"""
        # Validate UUID format
        if not company_id or len(company_id) != 8:
            raise ValidationError("Invalid company ID format")
        
        if current_employee.company_id != company_id or current_employee.role != "admin":
            raise ValidationError("Access denied")
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValidationError("Company not found")
        
        # Update settings
        current_settings = company.settings or {}
        new_settings = settings.dict(exclude_unset=True, exclude_none=True)
        
        # Merge with existing settings
        for key, value in new_settings.items():
            if isinstance(value, dict) and key in current_settings:
                current_settings[key].update(value)
            else:
                current_settings[key] = value
        
        company.settings = current_settings
        self.db.commit()
        
        log_action(
            current_employee.id,
            "company_settings_updated",
            f"Updated settings for company {company.company_name}"
        )
        
        return {"message": "Settings updated successfully", "settings": company.settings}
    
    def get_company_stats(self, company_id: str, current_employee: Employee) -> CompanyStats:
        """Get company statistics"""
        # Validate UUID format
        if not company_id or len(company_id) != 8:
            raise ValidationError("Invalid company ID format")
        
        if current_employee.company_id != company_id:
            raise ValidationError("Access denied")
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValidationError("Company not found")
        
        # Get counts
        employee_count = self.db.query(Employee).filter(
            Employee.company_id == company_id,
            Employee.is_active == True
        ).count()
        
        customer_count = self.db.query(Customer).filter(
            Customer.company_id == company_id
        ).count()
        
        campaign_count = self.db.query(Campaign).filter(
            Campaign.company_id == company_id
        ).count()
        
        # Get email statistics (you may need to implement this based on your tracking)
        total_emails_sent = 0  # Implement based on your tracking system
        current_month_emails = 0  # Implement based on your tracking system
        
        # Get last activity
        last_activity = self.db.query(func.max(Employee.created_at)).filter(
            Employee.company_id == company_id
        ).scalar()
        
        return CompanyStats(
            company_id=company_id,
            employee_count=employee_count,
            customer_count=customer_count,
            campaign_count=campaign_count,
            total_emails_sent=total_emails_sent,
            current_month_emails=current_month_emails,
            storage_used_mb=0.0,  # Implement if needed
            last_activity=last_activity
        )
    
    def deactivate_company(self, company_id: str) -> bool:
        """Deactivate company (super admin only)"""
        # Validate UUID format
        if not company_id or len(company_id) != 8:
            raise ValidationError("Invalid company ID format")
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValidationError("Company not found")
        
        company.is_active = False
        
        # Deactivate all employees
        self.db.query(Employee).filter(Employee.company_id == company_id).update({
            "is_active": False
        })
        
        self.db.commit()
        
        return True
    
    def _format_company_response(self, company: Company) -> CompanyResponse:
        """Format company data for response"""
        # Get additional counts
        employee_count = self.db.query(Employee).filter(
            Employee.company_id == company.id,
            Employee.is_active == True
        ).count()
        
        customer_count = self.db.query(Customer).filter(
            Customer.company_id == company.id
        ).count()
        
        campaign_count = self.db.query(Campaign).filter(
            Campaign.company_id == company.id
        ).count()
        
        company_dict = {
            "id": company.id,  # UUID as string
            "company_name": company.company_name,
            "domain": company.domain,
            "industry": company.industry,
            "company_size": company.company_size,
            "website": company.website,
            "phone": company.phone,
            "country": company.country,
            "timezone": company.timezone,
            "business_type": company.business_type,
            "description": company.description,
            "primary_use_case": company.primary_use_case,
            "expected_monthly_emails": company.expected_monthly_emails,
            "is_active": company.is_active,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "settings": company.settings or {},
            "employee_count": employee_count,
            "customer_count": customer_count,
            "campaign_count": campaign_count
        }
        
        return CompanyResponse(**company_dict)