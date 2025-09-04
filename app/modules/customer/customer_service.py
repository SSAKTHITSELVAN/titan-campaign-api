# customer_service.py
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.logger import get_logger
from app.modules.customer.customer_models import Customer
from app.modules.customer.customer_schemas import (
    CustomerCreateRequest, 
    CustomerUpdateRequest,
    CustomerBulkCreateRequest
)
from typing import Optional, List, Tuple
import math

logger = get_logger("CustomerService")

async def create_customer(company_id: str, customer_data: CustomerCreateRequest, session: AsyncSession) -> Customer:
    """Create a new customer for the company"""
    try:
        # Check for duplicate email within the same company
        result = await session.execute(
            select(Customer).where(
                and_(Customer.company_id == company_id, Customer.email == customer_data.email)
            )
        )
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            raise HTTPException(status_code=400, detail="Customer with this email already exists for this company")
        
        # Create new customer
        new_customer = Customer(
            company_id=company_id,
            **customer_data.dict()
        )
        session.add(new_customer)
        await session.commit()
        await session.refresh(new_customer)
        
        logger.info(f"Created customer {new_customer.email} for company {company_id}")
        return new_customer
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def get_customer_by_id(customer_id: str, company_id: str, session: AsyncSession) -> Optional[Customer]:
    """Get customer by ID and company ID"""
    try:
        result = await session.execute(
            select(Customer).where(
                and_(Customer.id == customer_id, Customer.company_id == company_id)
            )
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def get_customers_by_company(
    company_id: str, 
    session: AsyncSession, 
    page: int = 1, 
    page_size: int = 50,
    search: Optional[str] = None,
    category: Optional[str] = None
) -> Tuple[List[Customer], int]:
    """Get paginated customers for a company with optional filtering"""
    try:
        # Base query
        query = select(Customer).where(Customer.company_id == company_id)
        
        # Add search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.description.ilike(search_term)
                )
            )
        
        # Add category filter
        if category:
            query = query.where(Customer.category == category)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Add pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(Customer.created_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await session.execute(query)
        customers = result.scalars().all()
        
        return customers, total
        
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def update_customer(
    customer_id: str, 
    company_id: str, 
    customer_data: CustomerUpdateRequest, 
    session: AsyncSession
) -> Customer:
    """Update customer information"""
    try:
        # Get existing customer
        customer = await get_customer_by_id(customer_id, company_id, session)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Check for duplicate email if email is being updated
        if customer_data.email and customer_data.email != customer.email:
            result = await session.execute(
                select(Customer).where(
                    and_(
                        Customer.company_id == company_id, 
                        Customer.email == customer_data.email,
                        Customer.id != customer_id
                    )
                )
            )
            existing_customer = result.scalar_one_or_none()
            
            if existing_customer:
                raise HTTPException(status_code=400, detail="Customer with this email already exists for this company")
        
        # Update fields
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        await session.commit()
        await session.refresh(customer)
        
        logger.info(f"Updated customer {customer_id} for company {company_id}")
        return customer
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def delete_customer(customer_id: str, company_id: str, session: AsyncSession) -> bool:
    """Delete a customer"""
    try:
        # Check if customer exists
        customer = await get_customer_by_id(customer_id, company_id, session)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Delete customer
        await session.execute(
            delete(Customer).where(
                and_(Customer.id == customer_id, Customer.company_id == company_id)
            )
        )
        await session.commit()
        
        logger.info(f"Deleted customer {customer_id} from company {company_id}")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting customer: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def bulk_create_customers(
    company_id: str, 
    bulk_data: CustomerBulkCreateRequest, 
    session: AsyncSession
) -> Tuple[List[Customer], List[dict], int, int]:
    """Create multiple customers at once"""
    created_customers = []
    failed_customers = []
    
    try:
        # Get existing emails for this company to avoid duplicates
        result = await session.execute(
            select(Customer.email).where(Customer.company_id == company_id)
        )
        existing_emails = {email[0] for email in result.fetchall()}
        
        for i, customer_data in enumerate(bulk_data.customers):
            try:
                # Check for duplicate within the batch and existing customers
                if customer_data.email in existing_emails:
                    failed_customers.append({
                        "index": i,
                        "email": customer_data.email,
                        "error": "Customer with this email already exists"
                    })
                    continue
                
                # Check for duplicate within the current batch
                batch_emails = [c.email for c in bulk_data.customers[:i]]
                if customer_data.email in batch_emails:
                    failed_customers.append({
                        "index": i,
                        "email": customer_data.email,
                        "error": "Duplicate email in batch"
                    })
                    continue
                
                # Create customer
                new_customer = Customer(
                    company_id=company_id,
                    **customer_data.dict()
                )
                session.add(new_customer)
                existing_emails.add(customer_data.email)  # Track for next iterations
                
            except Exception as e:
                failed_customers.append({
                    "index": i,
                    "email": customer_data.email if hasattr(customer_data, 'email') else 'unknown',
                    "error": str(e)
                })
        
        # Commit all valid customers
        await session.commit()
        
        # Refresh created customers to get their IDs
        result = await session.execute(
            select(Customer).where(Customer.company_id == company_id).order_by(Customer.created_at.desc())
        )
        all_customers = result.scalars().all()
        
        # Get only the newly created customers (approximate based on count)
        expected_created = len(bulk_data.customers) - len(failed_customers)
        created_customers = all_customers[:expected_created] if expected_created > 0 else []
        
        logger.info(f"Bulk created {len(created_customers)} customers for company {company_id}, {len(failed_customers)} failed")
        return created_customers, failed_customers, len(created_customers), len(failed_customers)
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in bulk create customers: {e}")
        raise HTTPException(status_code=500, detail="Database error during bulk creation")

async def get_customers_by_category(company_id: str, category: str, session: AsyncSession) -> List[Customer]:
    """Get all customers in a specific category for a company"""
    try:
        result = await session.execute(
            select(Customer).where(
                and_(Customer.company_id == company_id, Customer.category == category)
            ).order_by(Customer.name)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error fetching customers by category: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def get_customer_stats(company_id: str, session: AsyncSession) -> dict:
    """Get customer statistics for a company"""
    try:
        # Total customers
        total_result = await session.execute(
            select(func.count()).where(Customer.company_id == company_id)
        )
        total = total_result.scalar()
        
        # Customers by category
        category_result = await session.execute(
            select(Customer.category, func.count()).where(
                Customer.company_id == company_id
            ).group_by(Customer.category)
        )
        categories = {category: count for category, count in category_result.fetchall()}
        
        return {
            "total_customers": total,
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"Error fetching customer stats: {e}")
        raise HTTPException(status_code=500, detail="Database error")