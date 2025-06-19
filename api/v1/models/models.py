# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()

class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"

class DonationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class NewsletterStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    SCHEDULED = "scheduled"

class Admin(Base):
    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ADMIN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

# class Initiative(Base):
#     __tablename__ = "initiatives"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
#     title = Column(String, nullable=False)
#     description = Column(Text)
#     little_description = Column(String)
#     goal_amount = Column(Float, default=0.0)
#     raised_amount = Column(Float, default=0.0)
#     image_url = Column(String)
#     background_image_url = Column(String)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     # Relationship with donations
#     donations = relationship("Donation", back_populates="initiative")

class Donation(Base):
    __tablename__ = "donations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    donor_name = Column(String, nullable=False)
    donor_email = Column(String, nullable=False)
    donor_phone = Column(String)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(DonationStatus), default=DonationStatus.PENDING)
    payment_reference = Column(String, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    # initiative = relationship("Initiative", back_populates="donations")

class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    unsubscribed_at = Column(DateTime)

class Newsletter(Base):
    __tablename__ = "newsletters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    html_content = Column(Text)
    status = Column(SQLEnum(NewsletterStatus), default=NewsletterStatus.DRAFT)
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    created_by = Column(UUID(as_uuid=True), ForeignKey("admins.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    creator = relationship("Admin")

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, nullable=False)
    subject = Column(String, nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    template_type = Column(String)  # thank_you, welcome, newsletter
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
class Donor(Base):
    __tablename__ = "donors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)