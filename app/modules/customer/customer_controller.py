# customer_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.auth_controller import get_current_user
from app.modules.auth.auth_service import get_user_company
from app.modules.customer.customer_service import (
    create_customer,
    get_customer_by_id,
    get_customers_by_company,
    update_customer,
    delete_customer,
    bulk_create_customers,
    get_customers_by_category,
    get_customer_stats
)
from app.modules.customer.customer_schemas import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    CustomerResponse,
    CustomerListResponse,
    CustomerBulkCreateRequest,
    CustomerBulkResponse
)
from app.database.session import get_session
from app.core.logger import get_logger
from typing import Optional
import math

logger = get_logger("CustomerController")

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

async def get_user_company_id(user=Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> str:
    """Dependency to get current user's company ID"""
    uid = user["uid"]
    company = await get_user_company(uid, session)
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found. Please create a company profile first.")
    
    return company.id

@router.post("/", response_model=CustomerResponse)
async def create_new_customer(
    customer_data: CustomerCreateRequest,
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Create a new customer"""
    customer = await create_customer(company_id, customer_data, session)
    return CustomerResponse.from_orm(customer)

@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Get paginated list of customers with optional filtering"""
    customers, total = await get_customers_by_company(
        company_id, session, page, page_size, search, category
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return CustomerListResponse(
        customers=[CustomerResponse.from_orm(customer) for customer in customers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/stats")
async def get_customer_statistics(
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Get customer statistics for the company"""
    stats = await get_customer_stats(company_id, session)
    return stats

@router.get("/category/{category}", response_model=list[CustomerResponse])
async def get_customers_by_category_endpoint(
    category: str,
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Get all customers in a specific category"""
    customers = await get_customers_by_category(company_id, category, session)
    return [CustomerResponse.from_orm(customer) for customer in customers]

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific customer by ID"""
    customer = await get_customer_by_id(customer_id, company_id, session)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse.from_orm(customer)

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_existing_customer(
    customer_id: str,
    customer_data: CustomerUpdateRequest,
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Update an existing customer"""
    customer = await update_customer(customer_id, company_id, customer_data, session)
    return CustomerResponse.from_orm(customer)

@router.delete("/{customer_id}")
async def delete_existing_customer(
    customer_id: str,
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Delete a customer"""
    success = await delete_customer(customer_id, company_id, session)
    return {"message": "Customer deleted successfully"}

@router.post("/bulk", response_model=CustomerBulkResponse)
async def bulk_create_customers_endpoint(
    bulk_data: CustomerBulkCreateRequest,
    company_id: str = Depends(get_user_company_id),
    session: AsyncSession = Depends(get_session)
):
    """Create multiple customers at once"""
    created, failed, created_count, failed_count = await bulk_create_customers(
        company_id, bulk_data, session
    )
    
    return CustomerBulkResponse(
        created=[CustomerResponse.from_orm(customer) for customer in created],
        failed=failed,
        total_attempted=len(bulk_data.customers),
        total_created=created_count,
        total_failed=failed_count
    )