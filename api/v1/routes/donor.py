
# api/v1/routes/volunteer.py
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
from api.v1.models import Donor
from typing import List, Optional
from uuid import UUID

router = APIRouter()



class DonorCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None

class DonorResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DonorCRUD:
    @staticmethod
    def create_donor(db: Session, donor: DonorCreate) -> Donor:
        try:
            db_donor = Donor(
                full_name=donor.full_name,
                email=donor.email,
                phone=donor.phone
            )
            db.add(db_donor)
            db.commit()
            db.refresh(db_donor)
            return db_donor
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")

    @staticmethod
    def get_donor(db: Session, donor_id: UUID) -> Optional[Donor]:
        return db.query(Donor).filter(Donor.id == donor_id).first()

    @staticmethod
    def get_donors(db: Session, skip: int = 0, limit: int = 100) -> List[Donor]:
        return db.query(Donor).offset(skip).limit(limit).all()

    @staticmethod
    def delete_donor(db: Session, donor_id: UUID) -> bool:
        donor = db.query(Donor).filter(Donor.id == donor_id).first()
        if donor:
            db.delete(donor)
            db.commit()
            return True
        return False

@router.post("/", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(
    donor: DonorCreate,
    db: Session = Depends(get_db)
):
    """Create a new donor"""
    return DonorCRUD.create_donor(db=db, donor=donor)

@router.get("/", response_model=List[DonorResponse])
async def get_all_donors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all donors"""
    donors = DonorCRUD.get_donors(db=db, skip=skip, limit=limit)
    return donors

@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(
    donor_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific donor by ID"""
    donor = DonorCRUD.get_donor(db=db, donor_id=donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found"
        )
    return donor

@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_donor(
    donor_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a donor by ID"""
    deleted = DonorCRUD.delete_donor(db=db, donor_id=donor_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found"
        )



