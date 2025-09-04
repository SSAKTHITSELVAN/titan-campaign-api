"""
Script to seed the database with initial data for testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.connection import SessionLocal, create_tables
from database.models import Company, Employee, Customer
from utils.security import get_password_hash

def seed_database():
    """Seed database with initial test data"""
    db = SessionLocal()
    
    try:
        # Create tables
        create_tables()
        
        # Check if companies already exist
        existing_companies = db.query(Company).all()
        if existing_companies:
            print("⚠️  Companies already exist in database. Skipping company creation.")
            created_companies = existing_companies
        else:
            # Create test companies using the CompanyService
            from app.modules.companies.compaines_services import CompanyService
            
            company_service = CompanyService(db)
            created_companies = []
            
            companies_data = [
                {
                    "company_name": "Acme Corporation",
                    "domain": "acme.com",
                    "industry": "Technology",
                    "company_size": "51-200",
                    "website": "https://acme.com",
                    "phone": "+1234567890",
                    "country": "United States",
                    "timezone": "America/New_York",
                    "business_type": "B2B",
                    "description": "Leading technology solutions provider",
                    "primary_use_case": "marketing",
                    "expected_monthly_emails": "10K-50K",
                    "admin_name": "Admin User",
                    "admin_email": "admin@acme.com",
                    "admin_password": "admin123"
                },
                {
                    "company_name": "Healthcare Plus",
                    "domain": "healthcareplus.com",
                    "industry": "Healthcare",
                    "company_size": "11-50",
                    "website": "https://healthcareplus.com",
                    "phone": "+1987654321",
                    "country": "Canada",
                    "timezone": "America/Toronto",
                    "business_type": "B2C",
                    "description": "Comprehensive healthcare solutions",
                    "primary_use_case": "newsletters",
                    "expected_monthly_emails": "1K-10K",
                    "admin_name": "Healthcare Admin",
                    "admin_email": "admin@healthcareplus.com",
                    "admin_password": "healthcare123"
                }
            ]
            
            for company_data in companies_data:
                try:
                    # Use CompanyCreate schema for validation
                    from app.modules.companies.compaines_schemas import CompanyCreate
                    company_create = CompanyCreate(**company_data)
                    
                    result = company_service.create_company(company_create)
                    created_companies.append(result["company"])
                    print(f"✅ Created company: {company_data['company_name']}")
                    
                except Exception as e:
                    print(f"⚠️  Company {company_data['company_name']} might already exist: {e}")
                    # Try to find existing company
                    existing = db.query(Company).filter(Company.domain == company_data["domain"]).first()
                    if existing:
                        created_companies.append(existing)
            
            if not created_companies:
                # Fallback: get existing companies
                created_companies = db.query(Company).all()
        
        # Create additional employees for existing companies (if not already created by CompanyService)
        additional_employees_data = [
            # Additional Acme Corporation employees
            {
                "company_id": created_companies[0].id,
                "name": "Marketing Manager",
                "email": "marketing@acme.com",
                "password": "marketing123",
                "role": "marketing"
            },
            {
                "company_id": created_companies[0].id,
                "name": "Data Analyst",
                "email": "analyst@acme.com",
                "password": "analyst123",
                "role": "analyst"
            }
        ]
        
        # Only add additional employees if they don't exist
        if len(created_companies) > 1:
            additional_employees_data.append({
                "company_id": created_companies[1].id,
                "name": "Communications Lead",
                "email": "comms@healthcareplus.com",
                "password": "comms123",
                "role": "marketing"
            })
        
        for employee_data in additional_employees_data:
            # Check if employee already exists
            existing_employee = db.query(Employee).filter(
                Employee.email == employee_data["email"]
            ).first()
            
            if not existing_employee:
                employee = Employee(
                    company_id=employee_data["company_id"],
                    name=employee_data["name"],
                    email=employee_data["email"],
                    password_hash=get_password_hash(employee_data["password"]),
                    role=employee_data["role"]
                )
                db.add(employee)
                print(f"✅ Created employee: {employee_data['name']}")
            else:
                print(f"⚠️  Employee {employee_data['name']} already exists")
        
        # Create test customers for each company
        if len(created_companies) >= 1:
            customers_data = [
                # Acme Corporation customers
                {
                    "company_id": created_companies[0].id,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "location": "New York",
                    "tags": ["vip", "enterprise"]
                },
                {
                    "company_id": created_companies[0].id,
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "phone": "+1234567891",
                    "location": "California",
                    "tags": ["premium"]
                },
                {
                    "company_id": created_companies[0].id,
                    "name": "Bob Johnson",
                    "email": "bob@example.com",
                    "phone": "+1234567892",
                    "location": "Texas",
                    "tags": ["standard"]
                }
            ]
            
            # Add Healthcare Plus customers if second company exists
            if len(created_companies) >= 2:
                customers_data.extend([
                    {
                        "company_id": created_companies[1].id,
                        "name": "Alice Brown",
                        "email": "alice@patient.com",
                        "phone": "+1234567893",
                        "location": "Toronto",
                        "tags": ["premium", "newsletter"]
                    },
                    {
                        "company_id": created_companies[1].id,
                        "name": "Charlie Wilson",
                        "email": "charlie@patient.com",
                        "phone": "+1234567894",
                        "location": "Vancouver",
                        "tags": ["standard", "health-tips"]
                    }
                ])
            
            for customer_data in customers_data:
                # Check if customer already exists
                existing_customer = db.query(Customer).filter(
                    Customer.email == customer_data["email"],
                    Customer.company_id == customer_data["company_id"]
                ).first()
                
                if not existing_customer:
                    customer = Customer(**customer_data)
                    db.add(customer)
                    print(f"✅ Created customer: {customer_data['name']}")
                else:
                    print(f"⚠️  Customer {customer_data['name']} already exists")
        
        db.commit()
        
        print("✅ Database seeded successfully!")
        print("\n🏢 Companies Created:")
        for i, company in enumerate(created_companies):
            company_name = getattr(company, 'company_name', None) or getattr(company, 'name', 'Unknown')
            domain = getattr(company, 'domain', 'Unknown')
            print(f"  {i+1}. {company_name} ({domain})")
        
        print("\n📧 Test Credentials:")
        if len(created_companies) >= 1:
            print("Acme Corporation:")
            print("  Admin: admin@acme.com / admin123")
            print("  Marketing: marketing@acme.com / marketing123")
            print("  Analyst: analyst@acme.com / analyst123")
        
        if len(created_companies) >= 2:
            print("\nHealthcare Plus:")
            print("  Admin: admin@healthcareplus.com / healthcare123")
            print("  Marketing: comms@healthcareplus.com / comms123")
        
        print("\n🔗 API Endpoints:")
        print("  Create Company: POST /api/companies/")
        print("  Login: POST /api/auth/login")
        print("  Company Details: GET /api/companies/me")
        print("  Documentation: http://localhost:8000/docs")
        print("  Server: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()