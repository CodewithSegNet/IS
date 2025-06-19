from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.db.database import get_db

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.v1.models import Volunteer
from typing import List, Optional
from uuid import UUID

router = APIRouter()



class VolunteerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None

class VolunteerResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Add this new model for stats response
class VolunteerStatsResponse(BaseModel):
    total_volunteers: int
    active_volunteers: int




class VolunteerCRUD:
    @staticmethod
    def create_volunteer(db: Session, volunteer: VolunteerCreate) -> Volunteer:
        try:
            db_volunteer = Volunteer(
                full_name=volunteer.full_name,
                email=volunteer.email,
                phone=volunteer.phone
            )
            db.add(db_volunteer)
            db.commit()
            db.refresh(db_volunteer)
            return db_volunteer
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")

    @staticmethod
    def get_volunteer(db: Session, volunteer_id: UUID) -> Optional[Volunteer]:
        return db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    @staticmethod
    def get_volunteers(db: Session, skip: int = 0, limit: int = 100) -> List[Volunteer]:
        return db.query(Volunteer).offset(skip).limit(limit).all()

    @staticmethod
    def delete_volunteer(db: Session, volunteer_id: UUID) -> bool:
        volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
        if volunteer:
            db.delete(volunteer)
            db.commit()
            return True
        return False

    # Add this new method for stats
    @staticmethod
    def get_volunteer_stats(db: Session) -> dict:
        total_volunteers = db.query(Volunteer).count()
        active_volunteers = db.query(Volunteer).filter(Volunteer.is_active == True).count()
        return {
            "total_volunteers": total_volunteers,
            "active_volunteers": active_volunteers
        }



@router.post("/", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
async def create_volunteer(
    volunteer: VolunteerCreate,
    db: Session = Depends(get_db)
):
    """Create a new volunteer"""
    return VolunteerCRUD.create_volunteer(db=db, volunteer=volunteer)

@router.get("/", response_model=List[VolunteerResponse])
async def get_all_volunteers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all volunteers"""
    volunteers = VolunteerCRUD.get_volunteers(db=db, skip=skip, limit=limit)
    return volunteers

# Add this new stats endpoint
@router.get("/stats/total", response_model=VolunteerStatsResponse)
async def get_volunteer_stats(db: Session = Depends(get_db)):
    """Get volunteer statistics"""
    stats = VolunteerCRUD.get_volunteer_stats(db=db)
    return stats

@router.get("/{volunteer_id}", response_model=VolunteerResponse)
async def get_volunteer(
    volunteer_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific volunteer by ID"""
    volunteer = VolunteerCRUD.get_volunteer(db=db, volunteer_id=volunteer_id)
    if volunteer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )
    return volunteer

@router.delete("/{volunteer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volunteer(
    volunteer_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a volunteer by ID"""
    deleted = VolunteerCRUD.delete_volunteer(db=db, volunteer_id=volunteer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer not found"
        )