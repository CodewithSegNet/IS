from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid
from api.v1.models import Subscriber
from api.db.database import get_db

router = APIRouter()

# Pydantic models
class SubscriberCreate(BaseModel):
    email: EmailStr

class SubscriberResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    subscribed_at: datetime
    unsubscribed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscriberUpdate(BaseModel):
    is_active: Optional[bool] = None

# Public endpoint for subscription
@router.post("/", response_model=dict)
async def subscribe(subscriber: SubscriberCreate, db: Session = Depends(get_db)):
    """
    Subscribe a new email to the newsletter
    """
    try:
        # Check if email already exists
        existing_subscriber = db.query(Subscriber).filter(
            Subscriber.email == subscriber.email
        ).first()
        
        if existing_subscriber:
            if existing_subscriber.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already subscribed"
                )
            else:
                # Reactivate existing subscriber
                existing_subscriber.is_active = True
                existing_subscriber.subscribed_at = datetime.utcnow()
                existing_subscriber.unsubscribed_at = None
                db.commit()
                return {"message": "Successfully resubscribed to newsletter"}
        
        # Create new subscriber
        db_subscriber = Subscriber(
            email=subscriber.email,
            is_active=True,
            subscribed_at=datetime.utcnow()
        )
        db.add(db_subscriber)
        db.commit()
        
        return {"message": "Successfully subscribed to newsletter"}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already subscribed"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to subscribe"
        )

# Admin endpoints (add authentication/authorization as needed)
@router.get("/", response_model=List[SubscriberResponse])
async def get_all_subscribers(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all subscribers (admin only)
    """
    query = db.query(Subscriber)
    
    if active_only:
        query = query.filter(Subscriber.is_active == True)
    
    subscribers = query.offset(skip).limit(limit).all()
    return subscribers

@router.get("/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(subscriber_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a specific subscriber by ID (admin only)
    """
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
        )
    return subscriber

@router.put("/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: uuid.UUID, 
    subscriber_update: SubscriberUpdate,
    db: Session = Depends(get_db)
):
    """
    Update subscriber status (admin only)
    """
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
        )
    
    if subscriber_update.is_active is not None:
        subscriber.is_active = subscriber_update.is_active
        if not subscriber_update.is_active:
            subscriber.unsubscribed_at = datetime.utcnow()
        else:
            subscriber.unsubscribed_at = None
    
    db.commit()
    db.refresh(subscriber)
    return subscriber

@router.delete("/{subscriber_id}")
async def delete_subscriber(subscriber_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a subscriber (admin only)
    """
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscriber not found"
        )
    
    db.delete(subscriber)
    db.commit()
    return {"message": "Subscriber deleted successfully"}

@router.post("/unsubscribe")
async def unsubscribe(subscriber: SubscriberCreate, db: Session = Depends(get_db)):
    """
    Unsubscribe an email from the newsletter
    """
    db_subscriber = db.query(Subscriber).filter(
        Subscriber.email == subscriber.email
    ).first()
    
    if not db_subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found in our subscription list"
        )
    
    if not db_subscriber.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already unsubscribed"
        )
    
    db_subscriber.is_active = False
    db_subscriber.unsubscribed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Successfully unsubscribed from newsletter"}

# Statistics endpoint
@router.get("/stats/summary")
async def get_subscriber_stats(db: Session = Depends(get_db)):
    """
    Get subscriber statistics (admin only)
    """
    total_subscribers = db.query(Subscriber).count()
    active_subscribers = db.query(Subscriber).filter(Subscriber.is_active == True).count()
    inactive_subscribers = total_subscribers - active_subscribers
    
    return {
        "total_subscribers": total_subscribers,
        "active_subscribers": active_subscribers,
        "inactive_subscribers": inactive_subscribers
    }