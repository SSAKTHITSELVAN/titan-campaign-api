
# ### database/models.py
# from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from database.connection import Base

# class Company(Base):
#     __tablename__ = "companies"
    
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(255), nullable=False)
#     domain = Column(String(255), unique=True, nullable=False)
#     settings = Column(JSON, default={})
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     employees = relationship("Employee", back_populates="company")
#     customers = relationship("Customer", back_populates="company")
#     campaigns = relationship("Campaign", back_populates="company")

# class Employee(Base):
#     __tablename__ = "employees"
    
#     id = Column(Integer, primary_key=True, index=True)
#     company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
#     name = Column(String(255), nullable=False)
#     email = Column(String(255), unique=True, nullable=False)
#     password_hash = Column(String(255), nullable=False)
#     role = Column(String(50), nullable=False)  # admin, marketing, analyst
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     company = relationship("Company", back_populates="employees")
#     created_campaigns = relationship("Campaign", back_populates="created_by")

# class Customer(Base):
#     __tablename__ = "customers"
    
#     id = Column(Integer, primary_key=True, index=True)
#     company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
#     name = Column(String(255), nullable=False)
#     email = Column(String(255), nullable=False)
#     phone = Column(String(50))
#     location = Column(String(255))
#     tags = Column(JSON, default=[])
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     company = relationship("Company", back_populates="customers")
#     campaign_recipients = relationship("CampaignRecipient", back_populates="customer")

# class Segment(Base):
#     __tablename__ = "segments"
    
#     id = Column(Integer, primary_key=True, index=True)
#     company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
#     name = Column(String(255), nullable=False)
#     filters = Column(JSON, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

# class Campaign(Base):
#     __tablename__ = "campaigns"
    
#     id = Column(Integer, primary_key=True, index=True)
#     company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
#     title = Column(String(255), nullable=False)
#     subject = Column(String(500), nullable=False)
#     body = Column(Text, nullable=False)
#     sender_email = Column(String(255), nullable=False)
#     status = Column(String(50), default="draft")  # draft, scheduled, sending, sent, failed
#     created_by_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
#     scheduled_at = Column(DateTime(timezone=True))
#     sent_at = Column(DateTime(timezone=True))
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
    
#     company = relationship("Company", back_populates="campaigns")
#     created_by = relationship("Employee", back_populates="created_campaigns")
#     recipients = relationship("CampaignRecipient", back_populates="campaign")

# class CampaignRecipient(Base):
#     __tablename__ = "campaign_recipients"
    
#     id = Column(Integer, primary_key=True, index=True)
#     campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
#     customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
#     status = Column(String(50), default="pending")  # pending, sent, opened, clicked, bounced
#     sent_at = Column(DateTime(timezone=True))
#     opened_at = Column(DateTime(timezone=True))
#     clicked_at = Column(DateTime(timezone=True))
    
#     campaign = relationship("Campaign", back_populates="recipients")
#     customer = relationship("Customer", back_populates="campaign_recipients")

# class Log(Base):
#     __tablename__ = "logs"
    
#     id = Column(Integer, primary_key=True, index=True)
#     timestamp = Column(DateTime(timezone=True), server_default=func.now())
#     employee_id = Column(Integer, ForeignKey("employees.id"))
#     action = Column(String(255), nullable=False)
#     details = Column(Text)



from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)  # 1-10, 11-50, 51-200, 201-1000, 1000+
    website = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    timezone = Column(String(50), default="UTC")
    business_type = Column(String(50), nullable=True)  # B2B, B2C, B2B2C
    description = Column(Text, nullable=True)
    primary_use_case = Column(String(100), nullable=True)  # newsletters, marketing, transactional
    expected_monthly_emails = Column(String(50), nullable=True)  # 1K-10K, 10K-50K, etc.
    
    # Legacy field for backward compatibility
    name = Column(String(255), nullable=True)  # Will be populated from company_name
    
    # Email settings
    settings = Column(JSON, default={})
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    employees = relationship("Employee", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    campaigns = relationship("Campaign", back_populates="company")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, marketing, analyst
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="employees")
    created_campaigns = relationship("Campaign", back_populates="created_by")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    location = Column(String(255))
    tags = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="customers")
    campaign_recipients = relationship("CampaignRecipient", back_populates="customer")

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    filters = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    sender_email = Column(String(255), nullable=False)
    status = Column(String(50), default="draft")  # draft, scheduled, sending, sent, failed
    created_by_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="campaigns")
    created_by = relationship("Employee", back_populates="created_campaigns")
    recipients = relationship("CampaignRecipient", back_populates="campaign")

class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, opened, clicked, bounced
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    
    campaign = relationship("Campaign", back_populates="recipients")
    customer = relationship("Customer", back_populates="campaign_recipients")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    employee_id = Column(Integer, ForeignKey("employees.id"))
    action = Column(String(255), nullable=False)
    details = Column(Text)