# customer_models.py
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modules.auth.auth_models import Base
import uuid

class Customer(Base):
    __tablename__ = "customers"
    
    # UUID as primary key (stored as string)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to company
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    
    # Customer information
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, default="subscriber")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Customer(id='{self.id}', email='{self.email}', name='{self.name}', company_id='{self.company_id}')>"