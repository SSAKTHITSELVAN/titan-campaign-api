# # auth_models.py
# from sqlalchemy import Column, String, DateTime, Text, Integer
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.sql import func
# import uuid

# Base = declarative_base()

# class User(Base):
#     __tablename__ = "users"
    
#     # Firebase UID as primary key (string)
#     uid = Column(String(128), primary_key=True, index=True)
#     email = Column(String(255), unique=True, index=True, nullable=False)
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
#     last_login = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
#     def __repr__(self):
#         return f"<User(uid='{self.uid}', email='{self.email}')>"


# class Company(Base):
#     __tablename__ = "companies"
    
#     # UUID as primary key (stored as string)
#     id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
#     # Foreign key to user
#     user_uid = Column(String(128), nullable=False, index=True)
    
#     # Company basic information
#     company_name = Column(String(255), nullable=False)
#     industry = Column(String(100), nullable=True)
#     company_size = Column(String(50), nullable=True)  # "1-10", "11-50", "51-200", "201-1000", "1000+"
#     website = Column(String(255), nullable=True)
    
#     # Contact information
#     phone = Column(String(20), nullable=True)
#     country = Column(String(100), nullable=True)
#     timezone = Column(String(50), nullable=True)
    
#     # Business details
#     business_type = Column(String(100), nullable=True)  # "B2B", "B2C", "B2B2C"
#     description = Column(Text, nullable=True)
    
#     # Email marketing specifics (like Zoho Campaigns)
#     primary_use_case = Column(String(100), nullable=True)  # "newsletters", "promotions", "transactional", "all"
#     expected_monthly_emails = Column(String(50), nullable=True)  # "0-1K", "1K-10K", "10K-50K", "50K+"
    
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
#     def __repr__(self):
#         return f"<Company(id='{self.id}', name='{self.company_name}', user_uid='{self.user_uid}')>"


# auth_models.py
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    # UUID as primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"


class UserToken(Base):
    __tablename__ = "user_tokens"
    
    # UUID as primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to user
    user_id = Column(String(36), nullable=False, index=True)
    
    # Token details
    access_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserToken(id='{self.id}', user_id='{self.user_id}')>"


class Company(Base):
    __tablename__ = "companies"
    
    # UUID as primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to user
    user_id = Column(String(36), nullable=False, index=True)
    
    # Company basic information
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)  # "1-10", "11-50", "51-200", "201-1000", "1000+"
    website = Column(String(255), nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Business details
    business_type = Column(String(100), nullable=True)  # "B2B", "B2C", "B2B2C"
    description = Column(Text, nullable=True)
    
    # Email marketing specifics
    primary_use_case = Column(String(100), nullable=True)  # "newsletters", "promotions", "transactional", "all"
    expected_monthly_emails = Column(String(50), nullable=True)  # "0-1K", "1K-10K", "10K-50K", "50K+"
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Company(id='{self.id}', name='{self.company_name}', user_id='{self.user_id}')>"