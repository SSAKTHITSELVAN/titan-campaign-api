
### modules/customers/services.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.exceptions import ValidationError
from core.logger import log_action
from database.models import Customer, Employee
from .schemas import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerImport

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_customer(self, customer_data: CustomerCreate, employee: Employee) -> CustomerResponse:
        # Check for duplicate email
        existing = self.db.query(Customer).filter(
            Customer.email == customer_data.email,
            Customer.company_id == employee.company_id
        ).first()
        
        if existing:
            raise ValidationError(f"Customer with email {customer_data.email} already exists")
        
        customer = Customer(
            company_id=employee.company_id,
            **customer_data.dict()
        )
        
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        
        log_action(employee.id, "customer_created", f"Created customer: {customer.email}")
        return CustomerResponse.from_orm(customer)
    
    def get_customers(self, employee: Employee, skip: int = 0, limit: int = 100) -> List[CustomerResponse]:
        customers = self.db.query(Customer).filter(
            Customer.company_id == employee.company_id
        ).offset(skip).limit(limit).all()
        
        return [CustomerResponse.from_orm(customer) for customer in customers]
    
    def get_customer(self, customer_id: int, employee: Employee) -> CustomerResponse:
        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.company_id == employee.company_id
        ).first()
        
        if not customer:
            raise ValidationError("Customer not found")
        
        return CustomerResponse.from_orm(customer)
    
    def update_customer(
        self, 
        customer_id: int, 
        customer_data: CustomerUpdate, 
        employee: Employee
    ) -> CustomerResponse:
        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.company_id == employee.company_id
        ).first()
        
        if not customer:
            raise ValidationError("Customer not found")
        
        # Update fields
        for field, value in customer_data.dict(exclude_unset=True).items():
            setattr(customer, field, value)
        
        self.db.commit()
        self.db.refresh(customer)
        
        log_action(employee.id, "customer_updated", f"Updated customer: {customer.email}")
        return CustomerResponse.from_orm(customer)
    
    def delete_customer(self, customer_id: int, employee: Employee) -> bool:
        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.company_id == employee.company_id
        ).first()
        
        if not customer:
            raise ValidationError("Customer not found")
        
        self.db.delete(customer)
        self.db.commit()
        
        log_action(employee.id, "customer_deleted", f"Deleted customer: {customer.email}")
        return True
    
    def import_customers(self, import_data: CustomerImport, employee: Employee) -> dict:
        results = {"created": 0, "skipped": 0, "errors": []}
        
        for customer_data in import_data.customers:
            try:
                # Check for duplicate
                existing = self.db.query(Customer).filter(
                    Customer.email == customer_data.email,
                    Customer.company_id == employee.company_id
                ).first()
                
                if existing:
                    results["skipped"] += 1
                    continue
                
                customer = Customer(
                    company_id=employee.company_id,
                    **customer_data.dict()
                )
                self.db.add(customer)
                results["created"] += 1
                
            except Exception as e:
                results["errors"].append(f"{customer_data.email}: {str(e)}")
        
        self.db.commit()
        log_action(
            employee.id, 
            "customers_imported", 
            f"Imported {results['created']} customers, skipped {results['skipped']}"
        )
        
        return results
    
    def search_customers(self, query: str, employee: Employee) -> List[CustomerResponse]:
        customers = self.db.query(Customer).filter(
            Customer.company_id == employee.company_id,
            or_(
                Customer.name.contains(query),
                Customer.email.contains(query),
                Customer.location.contains(query)
            )
        ).limit(50).all()
        
        return [CustomerResponse.from_orm(customer) for customer in customers]
