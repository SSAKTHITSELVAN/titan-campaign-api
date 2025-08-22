
### modules/auth/services.py
from datetime import timedelta
from sqlalchemy.orm import Session
from core.config import settings
from core.exceptions import AuthError
from core.logger import log_action
from database.models import Employee
from utils.security import verify_password, create_access_token
from .schemas import LoginRequest, LoginResponse

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_employee(self, login_data: LoginRequest) -> LoginResponse:
        employee = self.db.query(Employee).filter(
            Employee.email == login_data.email
        ).first()
        
        if not employee:
            log_action(None, "login_failed", f"Failed login attempt for {login_data.email}")
            raise AuthError("Invalid credentials")
        
        if not employee.is_active:
            raise AuthError("Account is inactive")
        
        if not verify_password(login_data.password, employee.password_hash):
            log_action(employee.id, "login_failed", f"Invalid password for {login_data.email}")
            raise AuthError("Invalid credentials")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(employee.id)},
            expires_delta=access_token_expires
        )
        
        log_action(employee.id, "login_success", f"Employee {employee.name} logged in")
        
        return LoginResponse(
            access_token=access_token,
            employee_id=employee.id,
            role=employee.role,
            name=employee.name
        )
