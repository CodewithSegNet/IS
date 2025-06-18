from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from api.v1.models.models import UserRole, DonationStatus, NewsletterStatus


class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    template_type: str

class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    template_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriberCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class SubscriberResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    subscribed_at: datetime

    class Config:
        from_attributes = True
