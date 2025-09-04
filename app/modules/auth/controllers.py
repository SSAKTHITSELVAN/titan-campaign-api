from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from utils.security import get_current_employee
from database.models import Employee
from .services import AuthService
from .schemas import LoginRequest, LoginResponse, EmployeeResponse

auth_router = APIRouter()

@auth_router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.authenticate_employee(login_data)

@auth_router.get("/me", response_model=EmployeeResponse)
async def get_current_user(current_employee: Employee = Depends(get_current_employee)):
    return current_employee

@auth_router.post("/logout")
async def logout(current_employee: Employee = Depends(get_current_employee)):
    # In a real implementation, you might want to blacklist the token
    return {"message": "Logged out successfully"}
