from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from api.v1.models.models import UserRole, DonationStatus, NewsletterStatus

# Auth Schemas
class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.ADMIN

class AdminResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: AdminResponse








class InitiativeCreate(BaseModel):
    title: str
    description: str
    little_description: str
    goal_amount: float
    image_url: Optional[str] = None
    background_image_url: Optional[str] = None

class InitiativeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    little_description: Optional[str] = None
    goal_amount: Optional[float] = None
    raised_amount: Optional[float] = None
    image_url: Optional[str] = None
    background_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class InitiativeResponse(BaseModel):
    id: int
    title: str
    description: str
    little_description: str
    goal_amount: float
    raised_amount: float
    progress: float
    image_url: Optional[str] = None
    background_image_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Subscriber Schemas
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

# Newsletter Schemas
class NewsletterCreate(BaseModel):
    subject: str
    content: str
    html_content: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class NewsletterResponse(BaseModel):
    id: int
    subject: str
    content: str
    html_content: Optional[str] = None
    status: NewsletterStatus
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Email Template Schemas
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

# Volunteer Schemas
class VolunteerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: Optional[str] = None
    availability: Optional[str] = None
    message: Optional[str] = None

class VolunteerResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    skills: Optional[str] = None
    availability: Optional[str] = None
    message: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = Tru




class VolunteerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: Optional[str] = None
    availability: Optional[str] = None
    message: Optional[str] = None

class VolunteerResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    skills: Optional[str] = None
    availability: Optional[str] = None
    message: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_donations: int
    total_amount_raised: float
    total_subscribers: int
    total_volunteers: int
    total_initiatives: int
    active_initiatives: int
    recent_donations: List[DonationResponse]
    monthly_donation_trend: List[dict]