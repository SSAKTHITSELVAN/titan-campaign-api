from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Employee
from utils.security import get_current_employee, require_role
from .customers_services import CustomerService
from .customers_schemas import (
    CustomerCreate, 
    CustomerUpdate, 
    CustomerResponse, 
    CustomerImport
)

customers_router = APIRouter()

@customers_router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CustomerService(db)
    return service.create_customer(customer_data, current_employee)

@customers_router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = CustomerService(db)
    return service.get_customers(current_employee, skip, limit)

@customers_router.get("/search", response_model=List[CustomerResponse])
async def search_customers(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = CustomerService(db)
    return service.search_customers(q, current_employee)

@customers_router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    service = CustomerService(db)
    return service.get_customer(customer_id, current_employee)

@customers_router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,  # Changed from int to str for UUID
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CustomerService(db)
    return service.update_customer(customer_id, customer_data, current_employee)

@customers_router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,  # Changed from int to str for UUID
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin"]))
):
    service = CustomerService(db)
    service.delete_customer(customer_id, current_employee)
    return {"message": "Customer deleted successfully"}

@customers_router.post("/import")
async def import_customers(
    import_data: CustomerImport,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(require_role(["admin", "marketing"]))
):
    service = CustomerService(db)
    results = service.import_customers(import_data, current_employee)
    return {"message": "Import completed", "results": results}