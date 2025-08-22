### modules/employees/services.py
from typing import List
from sqlalchemy.orm import Session
from core.exceptions import ValidationError, AuthError
from core.logger import log_action
from database.models import Employee
from utils.security import get_password_hash, verify_password
from .schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, PasswordChange

class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_employee(self, employee_data: EmployeeCreate, current_employee: Employee) -> EmployeeResponse:
        # Check for duplicate email
        existing = self.db.query(Employee).filter(
            Employee.email == employee_data.email
        ).first()
        
        if existing:
            raise ValidationError(f"Employee with email {employee_data.email} already exists")
        
        # Hash password
        password_hash = get_password_hash(employee_data.password)
        
        employee = Employee(
            company_id=current_employee.company_id,
            name=employee_data.name,
            email=employee_data.email,
            password_hash=password_hash,
            role=employee_data.role
        )
        
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        
        log_action(
            current_employee.id, 
            "employee_created", 
            f"Created employee: {employee.email} with role {employee.role}"
        )
        
        return EmployeeResponse.from_orm(employee)
    
    def get_employees(self, current_employee: Employee, skip: int = 0, limit: int = 100) -> List[EmployeeResponse]:
        employees = self.db.query(Employee).filter(
            Employee.company_id == current_employee.company_id
        ).offset(skip).limit(limit).all()
        
        return [EmployeeResponse.from_orm(employee) for employee in employees]
    
    def get_employee(self, employee_id: int, current_employee: Employee) -> EmployeeResponse:
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.company_id == current_employee.company_id
        ).first()
        
        if not employee:
            raise ValidationError("Employee not found")
        
        return EmployeeResponse.from_orm(employee)
    
    def update_employee(
        self, 
        employee_id: int, 
        employee_data: EmployeeUpdate, 
        current_employee: Employee
    ) -> EmployeeResponse:
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.company_id == current_employee.company_id
        ).first()
        
        if not employee:
            raise ValidationError("Employee not found")
        
        # Update fields
        for field, value in employee_data.dict(exclude_unset=True).items():
            setattr(employee, field, value)
        
        self.db.commit()
        self.db.refresh(employee)
        
        log_action(
            current_employee.id, 
            "employee_updated", 
            f"Updated employee: {employee.email}"
        )
        
        return EmployeeResponse.from_orm(employee)
    
    def change_password(
        self, 
        password_data: PasswordChange, 
        current_employee: Employee
    ) -> bool:
        # Verify current password
        if not verify_password(password_data.current_password, current_employee.password_hash):
            raise AuthError("Current password is incorrect")
        
        # Update password
        current_employee.password_hash = get_password_hash(password_data.new_password)
        self.db.commit()
        
        log_action(
            current_employee.id, 
            "password_changed", 
            f"Password changed for employee: {current_employee.email}"
        )
        
        return True
    
    def deactivate_employee(self, employee_id: int, current_employee: Employee) -> bool:
        if current_employee.id == employee_id:
            raise ValidationError("Cannot deactivate yourself")
        
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.company_id == current_employee.company_id
        ).first()
        
        if not employee:
            raise ValidationError("Employee not found")
        
        employee.is_active = False
        self.db.commit()
        
        log_action(
            current_employee.id, 
            "employee_deactivated", 
            f"Deactivated employee: {employee.email}"
        )
        
        return True
