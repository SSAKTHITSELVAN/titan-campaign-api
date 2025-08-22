### modules/employees/controllers.py
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Employee
from utils.security import get_current_employee, require_role
from .services import EmployeeService
from .schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    PasswordChange
)

employees_router = APIRouter()

@employees_router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    service = EmployeeService(db)
    return service.create_employee(employee_data, current_employee)

@employees_router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    service = EmployeeService(db)
    return service.get_employees(current_employee, skip, limit)

@employees_router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    service = EmployeeService(db)
    return service.get_employee(employee_id, current_employee)

@employees_router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    service = EmployeeService(db)
    return service.update_employee(employee_id, employee_data, current_employee)

@employees_router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = EmployeeService(db)
    service.change_password(password_data, current_employee)
    return {"message": "Password changed successfully"}

@employees_router.post("/{employee_id}/deactivate")
async def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    service = EmployeeService(db)
    service.deactivate_employee(employee_id, current_employee)
    return {"message": "Employee deactivated successfully"}
