from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config import settings
from core.exceptions import AuthError, ValidationError, EmailSendError
from core.logger import logger
from database.connection import create_tables
from modules.auth.controllers import auth_router
from modules.companies.controllers import companies_router
from modules.employees.controllers import employees_router
from modules.customers.controllers import customers_router
from modules.campaigns.controllers import campaigns_router
from modules.tracking.controllers import tracking_router

app = FastAPI(
    title="Email Campaign Management System",
    description="Company-based email campaign management with employee authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    logger.error(f"Auth error: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "auth_error"}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "validation_error"}
    )

@app.exception_handler(EmailSendError)
async def email_send_error_handler(request: Request, exc: EmailSendError):
    logger.error(f"Email send error: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "email_send_error"}
    )

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(companies_router, prefix="/api/companies", tags=["Companies"])
app.include_router(employees_router, prefix="/api/employees", tags=["Employees"])
app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
app.include_router(campaigns_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(tracking_router, prefix="/api/tracking", tags=["Tracking"])

@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info("Application started successfully")

@app.get("/")
async def root():
    return {
        "message": "Email Campaign Management System", 
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "companies": "/api/companies",
            "auth": "/api/auth",
            "employees": "/api/employees",
            "customers": "/api/customers",
            "campaigns": "/api/campaigns",
            "tracking": "/api/tracking"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)