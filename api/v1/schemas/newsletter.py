from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from api.v1.models.models import UserRole, DonationStatus, NewsletterStatus

        
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
