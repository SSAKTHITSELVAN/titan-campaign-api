# # auth_controller.py
# from fastapi import APIRouter, Depends, Header, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.modules.auth.auth_service import (
#     verify_firebase_token, 
#     create_or_update_user,
#     create_company,
#     get_user_company,
#     update_company
# )
# from app.modules.auth.auth_schemas import (
#     TokenVerifyResponse,
#     UserResponse,
#     CompanyCreateRequest,
#     CompanyUpdateRequest,
#     CompanyResponse
# )
# from app.database.session import get_session
# from app.core.logger import get_logger

# logger = get_logger("AuthController")

# router = APIRouter(
#     prefix="/auth",
#     tags=["Auth"]
# )

# def get_current_user(authorization: str = Header(...)):
#     """
#     Dependency to extract token from header and verify.
#     Header format: Authorization: Bearer <token>
#     """
#     if not authorization.startswith("Bearer "):
#         logger.warning("Authorization header missing or invalid")
#         raise HTTPException(status_code=401, detail="Invalid authorization header")
    
#     id_token = authorization.split(" ")[1]
#     user_info = verify_firebase_token(id_token)
#     return user_info

# @router.get("/verify", response_model=TokenVerifyResponse)
# async def verify_user(
#     user=Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     """
#     Verify Firebase token, create/update user in database, and return user info.
#     """
#     uid = user["uid"]
#     email = user["email"]
    
#     # Create or update user in database
#     db_user, is_new_user = await create_or_update_user(uid, email, session)
    
#     logger.info(f"Verified user: {email}, new_user: {is_new_user}")
#     return TokenVerifyResponse(
#         uid=uid,
#         email=email,
#         is_new_user=is_new_user
#     )

# @router.get("/profile", response_model=UserResponse)
# async def get_user_profile(
#     user=Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     """Get current user's profile information"""
#     from app.modules.auth.auth_service import get_user_by_uid
    
#     uid = user["uid"]
#     db_user = await get_user_by_uid(uid, session)
    
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     return UserResponse.from_orm(db_user)

# @router.post("/company", response_model=CompanyResponse)
# async def create_user_company(
#     company_data: CompanyCreateRequest,
#     user=Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     """Create company information for the current user"""
#     uid = user["uid"]
    
#     # Check if company already exists
#     existing_company = await get_user_company(uid, session)
#     if existing_company:
#         raise HTTPException(status_code=400, detail="Company already exists for this user")
    
#     new_company = await create_company(uid, company_data, session)
#     return CompanyResponse.from_orm(new_company)

# @router.get("/company", response_model=CompanyResponse)
# async def get_company_info(
#     user=Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     """Get current user's company information"""
#     uid = user["uid"]
#     company = await get_user_company(uid, session)
    
#     if not company:
#         raise HTTPException(status_code=404, detail="Company not found")
    
#     return CompanyResponse.from_orm(company)

# @router.put("/company", response_model=CompanyResponse)
# async def update_user_company(
#     company_data: CompanyUpdateRequest,
#     user=Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     """Update current user's company information"""
#     uid = user["uid"]
#     updated_company = await update_company(uid, company_data, session)
#     return CompanyResponse.from_orm(updated_company)

# @router.delete("/company")
# async def delete_user_company(
#     user=Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     """Delete current user's company information"""
#     uid = user["uid"]
    
#     try:
#         from sqlalchemy import select, delete
#         from app.modules.auth.auth_models import Company
        
#         # Check if company exists
#         result = await session.execute(select(Company).where(Company.user_uid == uid))
#         company = result.scalar_one_or_none()
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         # Delete company
#         await session.execute(delete(Company).where(Company.user_uid == uid))
#         await session.commit()
        
#         logger.info(f"Deleted company for user {uid}")
#         return {"message": "Company deleted successfully"}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         await session.rollback()
#         logger.error(f"Error deleting company: {e}")
#         raise HTTPException(status_code=500, detail="Database error")



# auth_controller.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_token,
    create_company,
    get_user_company,
    update_company
)
from app.modules.auth.auth_schemas import (
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
    LoginResponse,
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse
)
from app.database.session import get_session
from app.core.logger import get_logger

logger = get_logger("AuthController")

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

def get_current_user(authorization: str = Header(...)):
    """
    Dependency to extract token from header and verify.
    Header format: Authorization: Bearer <token>
    """
    if not authorization.startswith("Bearer "):
        logger.warning("Authorization header missing or invalid")
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    user_info = get_user_by_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_info

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user with email and password.
    """
    try:
        new_user = await create_user(user_data, session)
        logger.info(f"Registered new user: {new_user.email}")
        return UserResponse.from_orm(new_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=LoginResponse)
async def login_user(
    user_credentials: UserLoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Authenticate user with email and password, return access token.
    """
    try:
        user, token = await authenticate_user(user_credentials, session)
        logger.info(f"User logged in: {user.email}")
        return LoginResponse(
            user=UserResponse.from_orm(user),
            access_token=token,
            token_type="bearer"
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get current user's profile information"""
    from app.modules.auth.auth_service import get_user_by_id
    
    user_id = user["id"]
    db_user = await get_user_by_id(user_id, session)
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.from_orm(db_user)

@router.post("/company", response_model=CompanyResponse)
async def create_user_company(
    company_data: CompanyCreateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create company information for the current user"""
    user_id = user["id"]
    
    # Check if company already exists
    existing_company = await get_user_company(user_id, session)
    if existing_company:
        raise HTTPException(status_code=400, detail="Company already exists for this user")
    
    new_company = await create_company(user_id, company_data, session)
    return CompanyResponse.from_orm(new_company)

@router.get("/company", response_model=CompanyResponse)
async def get_company_info(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get current user's company information"""
    user_id = user["id"]
    company = await get_user_company(user_id, session)
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return CompanyResponse.from_orm(company)

@router.put("/company", response_model=CompanyResponse)
async def update_user_company(
    company_data: CompanyUpdateRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update current user's company information"""
    user_id = user["id"]
    updated_company = await update_company(user_id, company_data, session)
    return CompanyResponse.from_orm(updated_company)

@router.delete("/company")
async def delete_user_company(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete current user's company information"""
    user_id = user["id"]
    
    try:
        from sqlalchemy import select, delete
        from app.modules.auth.auth_models import Company
        
        # Check if company exists
        result = await session.execute(select(Company).where(Company.user_id == user_id))
        company = result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Delete company
        await session.execute(delete(Company).where(Company.user_id == user_id))
        await session.commit()
        
        logger.info(f"Deleted company for user {user_id}")
        return {"message": "Company deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting company: {e}")
        raise HTTPException(status_code=500, detail="Database error")