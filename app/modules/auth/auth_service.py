# # auth_service.py
# import firebase_admin
# from firebase_admin import auth, credentials
# from fastapi import HTTPException, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from sqlalchemy.sql import func
# from app.core.logger import get_logger
# from app.database.session import get_session
# from app.modules.auth.auth_models import User, Company
# from app.modules.auth.auth_schemas import CompanyCreateRequest, CompanyUpdateRequest
# from typing import Optional

# logger = get_logger("AuthService")

# # Initialize Firebase Admin SDK (singleton)
# cred = credentials.Certificate("app/modules/auth/serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

# def verify_firebase_token(id_token: str):
#     """
#     Verify Firebase JWT token and return user info.
#     Raises HTTPException if invalid or expired.
#     """
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         uid = decoded_token.get("uid")
#         email = decoded_token.get("email")
#         logger.info(f"Token verified successfully for uid: {uid}, email: {email}")
#         return {"uid": uid, "email": email}
#     except Exception as e:
#         logger.error(f"Token verification failed: {e}")
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

# async def create_or_update_user(uid: str, email: str, session: AsyncSession):
#     """
#     Create user if doesn't exist, update last_login if exists.
#     Returns tuple (user, is_new_user)
#     """
#     try:
#         # Check if user exists
#         result = await session.execute(select(User).where(User.uid == uid))
#         user = result.scalar_one_or_none()
        
#         if user:
#             # Update last login
#             user.last_login = func.now()
#             await session.commit()
#             logger.info(f"Updated last login for existing user: {uid}")
#             return user, False
#         else:
#             # Create new user
#             new_user = User(uid=uid, email=email)
#             session.add(new_user)
#             await session.commit()
#             await session.refresh(new_user)
#             logger.info(f"Created new user: {uid}")
#             return new_user, True
            
#     except Exception as e:
#         await session.rollback()
#         logger.error(f"Error creating/updating user: {e}")
#         raise HTTPException(status_code=500, detail="Database error")

# async def get_user_by_uid(uid: str, session: AsyncSession) -> Optional[User]:
#     """Get user by Firebase UID"""
#     try:
#         result = await session.execute(select(User).where(User.uid == uid))
#         return result.scalar_one_or_none()
#     except Exception as e:
#         logger.error(f"Error fetching user: {e}")
#         raise HTTPException(status_code=500, detail="Database error")

# async def create_company(uid: str, company_data: CompanyCreateRequest, session: AsyncSession) -> Company:
#     """Create a new company for the user"""
#     try:
#         # Check if user exists
#         user = await get_user_by_uid(uid, session)
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Create company
#         new_company = Company(
#             user_uid=uid,
#             **company_data.dict()
#         )
#         session.add(new_company)
#         await session.commit()
#         await session.refresh(new_company)
        
#         logger.info(f"Created company for user {uid}: {new_company.company_name}")
#         return new_company
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         await session.rollback()
#         logger.error(f"Error creating company: {e}")
#         raise HTTPException(status_code=500, detail="Database error")

# async def get_user_company(uid: str, session: AsyncSession) -> Optional[Company]:
#     """Get user's company information"""
#     try:
#         result = await session.execute(select(Company).where(Company.user_uid == uid))
#         return result.scalar_one_or_none()
#     except Exception as e:
#         logger.error(f"Error fetching company: {e}")
#         raise HTTPException(status_code=500, detail="Database error")

# async def update_company(uid: str, company_data: CompanyUpdateRequest, session: AsyncSession) -> Company:
#     """Update user's company information"""
#     try:
#         # Get existing company
#         result = await session.execute(select(Company).where(Company.user_uid == uid))
#         company = result.scalar_one_or_none()
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         # Update fields
#         update_data = company_data.dict(exclude_unset=True)
#         for field, value in update_data.items():
#             setattr(company, field, value)
        
#         await session.commit()
#         await session.refresh(company)
        
#         logger.info(f"Updated company for user {uid}")
#         return company
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         await session.rollback()
#         logger.error(f"Error updating company: {e}")
#         raise HTTPException(status_code=500, detail="Database error")


# auth_service.py
import secrets
import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from app.core.logger import get_logger
from app.modules.auth.auth_models import User, UserToken, Company
from app.modules.auth.auth_schemas import UserCreateRequest, UserLoginRequest, CompanyCreateRequest, CompanyUpdateRequest
from typing import Optional, Tuple

logger = get_logger("AuthService")

# Token configuration
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days
TOKEN_LENGTH = 32

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, pwd_hash = hashed_password.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except ValueError:
        return False

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(TOKEN_LENGTH)

async def create_user(user_data: UserCreateRequest, session: AsyncSession) -> User:
    """
    Create a new user with hashed password.
    Raises ValueError if user already exists.
    """
    try:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        logger.info(f"Created new user: {user_data.email}")
        return new_user
        
    except ValueError:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def authenticate_user(credentials: UserLoginRequest, session: AsyncSession) -> Tuple[User, str]:
    """
    Authenticate user and create access token.
    Returns tuple (user, access_token)
    Raises ValueError if authentication fails.
    """
    try:
        # Get user by email
        result = await session.execute(select(User).where(User.email == credentials.email))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Generate access token
        access_token = generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
        
        # Deactivate old tokens for this user
        await session.execute(
            select(UserToken).where(UserToken.user_id == user.id).where(UserToken.is_active == True)
        )
        old_tokens = await session.execute(select(UserToken).where(UserToken.user_id == user.id))
        for token in old_tokens.scalars():
            token.is_active = False
        
        # Create new token
        user_token = UserToken(
            user_id=user.id,
            access_token=access_token,
            expires_at=expires_at
        )
        session.add(user_token)
        
        # Update last login
        user.last_login = func.now()
        
        await session.commit()
        
        logger.info(f"User authenticated: {user.email}")
        return user, access_token
        
    except ValueError:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(status_code=500, detail="Database error")

def get_user_by_token(token: str) -> Optional[dict]:
    """
    Verify token and return user info.
    This is a synchronous function for the dependency.
    """
    # In a real application, you'd want to make this async and check the database
    # For now, we'll return a simple implementation
    # You should implement proper async token verification
    return {"id": "user-id-from-token", "email": "user@example.com"}

async def get_user_by_id(user_id: str, session: AsyncSession) -> Optional[User]:
    """Get user by ID"""
    try:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def verify_token(token: str, session: AsyncSession) -> Optional[User]:
    """Verify access token and return user"""
    try:
        # Get token from database
        result = await session.execute(
            select(UserToken).where(UserToken.access_token == token)
            .where(UserToken.is_active == True)
            .where(UserToken.expires_at > datetime.utcnow())
        )
        user_token = result.scalar_one_or_none()
        
        if not user_token:
            return None
        
        # Get user
        user_result = await session.execute(select(User).where(User.id == user_token.user_id))
        user = user_result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

async def create_company(user_id: str, company_data: CompanyCreateRequest, session: AsyncSession) -> Company:
    """Create a new company for the user"""
    try:
        # Check if user exists
        user = await get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create company
        new_company = Company(
            user_id=user_id,
            **company_data.dict()
        )
        session.add(new_company)
        await session.commit()
        await session.refresh(new_company)
        
        logger.info(f"Created company for user {user_id}: {new_company.company_name}")
        return new_company
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating company: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def get_user_company(user_id: str, session: AsyncSession) -> Optional[Company]:
    """Get user's company information"""
    try:
        result = await session.execute(select(Company).where(Company.user_id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching company: {e}")
        raise HTTPException(status_code=500, detail="Database error")

async def update_company(user_id: str, company_data: CompanyUpdateRequest, session: AsyncSession) -> Company:
    """Update user's company information"""
    try:
        # Get existing company
        result = await session.execute(select(Company).where(Company.user_id == user_id))
        company = result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Update fields
        update_data = company_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        
        await session.commit()
        await session.refresh(company)
        
        logger.info(f"Updated company for user {user_id}")
        return company
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating company: {e}")
        raise HTTPException(status_code=500, detail="Database error")