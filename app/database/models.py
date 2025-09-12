# models.py
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean , Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import uuid

class Company(Base):
    __tablename__ = "companies"
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
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
    
    whatsapp_templates = relationship("WhatsAppTemplate", back_populates="company")

class Employee(Base):
    __tablename__ = "employees"
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
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
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
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
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    filters = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Campaign(Base):
    __tablename__ = "campaigns"
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    company_id = Column(String(8), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    sender_email = Column(String(255), nullable=False)
    status = Column(String(50), default="draft")  # draft, scheduled, sending, sent, failed
    created_by_employee_id = Column(String(36), ForeignKey("employees.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="campaigns")
    created_by = relationship("Employee", back_populates="created_campaigns")
    recipients = relationship("CampaignRecipient", back_populates="campaign")
    
    channel = Column(String(20), default="email")
    template_name = Column(String, nullable=True)

class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, opened, clicked, bounced
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    
    campaign = relationship("Campaign", back_populates="recipients")
    customer = relationship("Customer", back_populates="campaign_recipients")
    
    recipient_phone = Column(String(50), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    seen_at = Column(DateTime(timezone=True), nullable=True)
    clicked = Column(Boolean, default=False)
    clicked_payload = Column(String(500), nullable=True)
    message_id = Column(String(100), nullable=True)

class Log(Base):
    __tablename__ = "logs"
    
    # UUID as primary key
    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    employee_id = Column(String(36), ForeignKey("employees.id"))
    action = Column(String(255), nullable=False)
    details = Column(Text)

class WhatsAppTemplate(Base):
    __tablename__ = "whatsapp_templates"

    id = Column(String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8], index=True)
    company_id = Column(String(8), ForeignKey("companies.id"))
    name = Column(String(255), index=True)
    language = Column(String(10), default="en_US")
    category = Column(String(50), default="MARKETING")
    status = Column(String(50), default="draft")
    body = Column(Text, nullable=False)
    header = Column(Text, nullable=True)
    footer = Column(Text, nullable=True)
    buttons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # NEW FIELDS FOR MEDIA SUPPORT
    header_type = Column(String(20), default="text")  # text, image, video, document, location, none
    header_media_url = Column(String(500), nullable=True)  # Public URL for media
    header_media_id = Column(String(100), nullable=True)  # Meta media ID after upload
    header_location_data = Column(JSON, nullable=True)  # For location headers: {lat, lng, name, address}
    body_parameters_count = Column(Integer, default=0)  # type: ignore # Number of {{1}}, {{2}} parameters in body
    button_parameters = Column(JSON, nullable=True)  # Button parameter configurations
    meta_template_id = Column(String(100), nullable=True)  # Meta's template ID after approval
    rejection_reason = Column(Text, nullable=True)  # If rejected by Meta
    
    company = relationship("Company", back_populates="whatsapp_templates")