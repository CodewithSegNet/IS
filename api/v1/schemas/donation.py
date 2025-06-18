from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from api.v1.models.models import UserRole, DonationStatus, NewsletterStatus
    
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID




class DonationCreate(BaseModel):
    title: str
    donor_name: str
    donor_email: EmailStr
    donor_phone: Optional[str] = None
    amount: float
    initiative_id: int
    is_anonymous: bool = False
    message: Optional[str] = None

# class DonationResponse(BaseModel):
#     id: int
#     donor_name: str
#     donor_email: str
#     donor_phone: Optional[str] = None
#     amount: float
#     initiative_id: int
#     status: DonationStatus
#     payment_reference: Optional[str] = None
#     is_anonymous: bool
#     message: Optional[str] = None
#     created_at: datetime

#     class Config:
#         from_attributes = True



# class DashboardStats(BaseModel):
#     total_donations: int
#     total_amount_raised: float
#     total_subscribers: int
#     total_volunteers: int
#     total_initiatives: int
#     active_initiatives: int
#     recent_donations: List[DonationResponse]
#     monthly_donation_trend: List[dict]
    
    
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
    
    


class DonationBase(BaseModel):
    donor_name: str
    donor_email: EmailStr
    donor_phone: str
    title: str
    amount: float
    initiative_id: Optional[UUID] = None
    is_anonymous: bool = False
    message: Optional[str] = None

class DonationCreate(DonationBase):
    pass

class DonationUpdate(BaseModel):
    donor_name: Optional[str] = None
    donor_email: Optional[EmailStr] = None
    donor_phone: Optional[str] = None
    amount: Optional[float] = None
    title: str
    initiative_id: Optional[UUID] = None
    is_anonymous: Optional[bool] = None
    message: Optional[str] = None
    status: Optional[str] = None
    payment_reference: Optional[str] = None

class DonationResponse(DonationBase):
    id: UUID
    status: str
    payment_reference: Optional[str]
    created_at: datetime
    initiative: Optional[dict] = None

    class Config:
        from_attributes = True

class DonationListResponse(BaseModel):
    donations: list[DonationResponse]
    total: int
    page: int
    limit: int

# Frontend compatible schema
class FrontendDonationCreate(BaseModel):
    title: str
    amount: float
    donor_name: str
    donor_email: EmailStr
    donor_phone: str
    donor_country: str = "Nigeria"
    payment_method: str = "bank_transfer"
    status: str = "pending"
    is_anonymous: bool = False
    message: Optional[str] = None