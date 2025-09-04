from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid
from core.exceptions import ValidationError
from core.logger import log_action
from database.models import Customer, Employee
from .customers_schemas import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerImport

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
            id=str(uuid.uuid4())[:8],  # Generate UUID for customer
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
    
    def get_customer(self, customer_id: str, employee: Employee) -> CustomerResponse:
        # Validate UUID format
        if not customer_id or len(customer_id) != 8:
            raise ValidationError("Invalid customer ID format")

        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.company_id == employee.company_id
        ).first()
        
        if not customer:
            raise ValidationError("Customer not found")
        
        return CustomerResponse.from_orm(customer)
    
    def update_customer(
        self, 
        customer_id: str, 
        customer_data: CustomerUpdate, 
        employee: Employee
    ) -> CustomerResponse:
        # Validate UUID format
        if not customer_id or len(customer_id) != 8:
            raise ValidationError("Invalid customer ID format")

        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.company_id == employee.company_id
        ).first()
        
        if not customer:
            raise ValidationError("Customer not found")
        
        # Check for duplicate email if email is being updated
        update_data = customer_data.dict(exclude_unset=True)
        if 'email' in update_data and update_data['email'] != customer.email:
            existing = self.db.query(Customer).filter(
                Customer.email == update_data['email'],
                Customer.company_id == employee.company_id,
                Customer.id != customer_id
            ).first()
            
            if existing:
                raise ValidationError(f"Customer with email {update_data['email']} already exists")
        
        # Update fields
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        self.db.commit()
        self.db.refresh(customer)
        
        log_action(employee.id, "customer_updated", f"Updated customer: {customer.email}")
        return CustomerResponse.from_orm(customer)
    
    def delete_customer(self, customer_id: str, employee: Employee) -> bool:
        # Validate UUID format
        if not customer_id or len(customer_id) != 8:
            raise ValidationError("Invalid customer ID format")

        customer = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.company_id == employee.company_id
        ).first()
        
        if not customer:
            raise ValidationError("Customer not found")
        
        customer_email = customer.email  # Store for logging
        
        self.db.delete(customer)
        self.db.commit()
        
        log_action(employee.id, "customer_deleted", f"Deleted customer: {customer_email}")
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
                    id=str(uuid.uuid4())[:8],  # Generate UUID for each imported customer
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