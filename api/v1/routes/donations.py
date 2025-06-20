from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import uuid

from api.v1.models import Donation, DonationStatus

from typing import Optional, List
from uuid import UUID
import os
import uuid
import shutil
from pathlib import Path

from api.db.database import get_db
from api.v1.schemas.donation import (
    DonationCreate,
    DonationUpdate,
    DonationResponse,
    DonationListResponse,
    FrontendDonationCreate
)

# Import settings to use proper configuration
from api.utils.settings import settings

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configure Cloudinary using settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = Path("./media")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
print(f"Upload directory exists: {UPLOAD_DIR.exists()}")
print(f"Files in directory: {list(UPLOAD_DIR.glob('*')) if UPLOAD_DIR.exists() else 'Directory not found'}")

# Debug: Print Cloudinary configuration (remove in production)
print(f"Cloudinary Config - Cloud Name: {settings.CLOUDINARY_CLOUD_NAME}")
print(f"Cloudinary Config - API Key: {settings.CLOUDINARY_API_KEY[:8]}..." if settings.CLOUDINARY_API_KEY else "API Key: None")
print(f"Cloudinary Config - API Secret: {'Set' if settings.CLOUDINARY_API_SECRET else 'Not Set'}")

def get_donation(db: Session, donation_id: UUID) -> Optional[Donation]:
    """Get a single donation by ID"""
    return db.query(Donation).filter(Donation.id == donation_id).first()

def get_donations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    title: Optional[str] = None
) -> List[Donation]:
    """Get multiple donations with optional filtering by title"""
    query = db.query(Donation)

    if title:
        query = query.filter(Donation.title == title)

    return query.order_by(desc(Donation.created_at)).offset(skip).limit(limit).all()

def count_donations(db: Session, title: Optional[str] = None) -> int:
    """Count total donations"""
    query = db.query(Donation)

    if title:
        query = query.filter(Donation.title == title)

    return query.count()

def create_donation(db: Session, donation: DonationCreate) -> Donation:
    """Create a new donation"""
    db_donation = Donation(
        id=uuid.uuid4(),
        title=donation.title,
        donor_name=donation.donor_name,
        donor_email=donation.donor_email,
        donor_phone=donation.donor_phone,
        amount=donation.amount,
        is_anonymous=donation.is_anonymous,
        message=donation.message,
        status=DonationStatus.PENDING
    )

    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)

    return db_donation

def create_donation_from_frontend(db: Session, donation: FrontendDonationCreate) -> Donation:
    """Create donation from frontend data"""
    db_donation = Donation(
        id=uuid.uuid4(),
        title=donation.title,
        donor_name=donation.donor_name,
        donor_email=donation.donor_email,
        donor_phone=donation.donor_phone,
        amount=donation.amount,
        is_anonymous=donation.is_anonymous,
        message=donation.message,
        status=DonationStatus.PENDING
    )

    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)

    return db_donation

def update_donation(db: Session, donation_id: UUID, donation_update: DonationUpdate) -> Optional[Donation]:
    """Update a donation"""
    db_donation = get_donation(db, donation_id)
    if not db_donation:
        return None

    update_data = donation_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_donation, field, value)

    db.commit()
    db.refresh(db_donation)
    return db_donation

def delete_donation(db: Session, donation_id: UUID) -> bool:
    """Delete a donation"""
    db_donation = get_donation(db, donation_id)
    if not db_donation:
        return False

    db.delete(db_donation)
    db.commit()
    return True

def get_donations_by_email(db: Session, email: str) -> List[Donation]:
    """Get all donations by donor email"""
    return db.query(Donation).filter(Donation.donor_email == email).order_by(desc(Donation.created_at)).all()

def get_total_donated_amount(db: Session, title: Optional[str] = None) -> float:
    """Get total amount donated"""
    query = db.query(Donation).filter(Donation.status == DonationStatus.COMPLETED)

    if title:
        query = query.filter(Donation.title == title)

    donations = query.all()
    return sum(donation.amount for donation in donations)

@router.get("/", response_model=DonationListResponse)
async def get_donations_endpoint(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of donations to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of donations to return"),
    title: Optional[str] = Query(None, description="Filter by donation title")
):
    """Get all donations with pagination and optional filtering"""
    try:
        donations = get_donations(db, skip=skip, limit=limit, title=title)
        total = count_donations(db, title=title)

        return DonationListResponse(
            donations=donations,
            total=total,
            page=skip // limit + 1,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving donations: {str(e)}")

@router.post("/donations", response_model=DonationResponse)
async def create_donation_endpoint(
    donation: FrontendDonationCreate,
    db: Session = Depends(get_db)
):
    """Create a new donation (Frontend compatible)"""
    try:
        # Validate amount
        if donation.amount <= 0:
            raise HTTPException(status_code=400, detail="Donation amount must be greater than 0")

        # Create donation
        db_donation = create_donation_from_frontend(db, donation)

        return DonationResponse(
            id=db_donation.id,
            title=db_donation.title,
            donor_name=db_donation.donor_name,
            donor_email=db_donation.donor_email,
            donor_phone=db_donation.donor_phone,
            amount=db_donation.amount,
            is_anonymous=db_donation.is_anonymous,
            message=db_donation.message,
            status=db_donation.status,
            payment_reference=db_donation.payment_reference,
            created_at=db_donation.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating donation: {str(e)}")

@router.post("/upload-receipt")
async def upload_receipt(
    receipt: UploadFile = File(...),
    donation_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload payment receipt for a donation using Cloudinary"""

    try:
        # Debug: Check if Cloudinary credentials are available
        if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
            print("Missing Cloudinary credentials:")
            print(f"Cloud Name: {'Set' if settings.CLOUDINARY_CLOUD_NAME else 'Missing'}")
            print(f"API Key: {'Set' if settings.CLOUDINARY_API_KEY else 'Missing'}")
            print(f"API Secret: {'Set' if settings.CLOUDINARY_API_SECRET else 'Missing'}")
            raise HTTPException(
                status_code=500,
                detail="Cloudinary configuration is incomplete. Please check your environment variables."
            )

        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
        if receipt.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG, PNG, and PDF files are allowed."
            )

        # Validate file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if receipt.size > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        # Get donation to retrieve title
        try:
            donation_uuid = UUID(donation_id)
            db_donation = get_donation(db, donation_uuid)
            if not db_donation:
                raise HTTPException(status_code=404, detail="Donation not found")

            donation_title = db_donation.title.replace(" ", "_").lower()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid donation ID format")

        # Generate unique public_id for Cloudinary
        unique_id = str(uuid.uuid4())
        public_id = f"receipts/{donation_title}_{unique_id}"

        try:
            # Determine resource type based on file content type
            resource_type = "image" if receipt.content_type.startswith("image/") else "raw"
            
            # Debug: Log upload parameters
            print(f"Uploading file: {receipt.filename}")
            print(f"Content type: {receipt.content_type}")
            print(f"Resource type: {resource_type}")
            print(f"Public ID: {public_id}")
            
            # Upload to Cloudinary with proper parameters
            upload_result = cloudinary.uploader.upload(
                receipt.file,
                public_id=public_id,
                folder="donation_receipts",
                resource_type=resource_type,
                overwrite=True,
                # Add file format handling for images
                **({"quality": "auto", "fetch_format": "auto"} if resource_type == "image" else {})
            )

            # Get the secure URL
            receipt_url = upload_result['secure_url']

            # Update database with Cloudinary URL
            db_donation.payment_reference = receipt_url
            db.commit()

            return JSONResponse(
                status_code=200,
                content={
                    "message": "Receipt uploaded successfully",
                    "filename": f"{donation_title}_{unique_id}",
                    "receipt_url": receipt_url,
                    "donation_id": donation_id,
                    "cloudinary_public_id": upload_result['public_id']
                }
            )

        except Exception as upload_error:
            db.rollback()
            print(f"Cloudinary upload error: {upload_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to cloud storage: {str(upload_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading receipt: {str(e)}")

@router.get("/media/{filename}")
async def serve_uploaded_file_with_mime(filename: str):
    """Serve uploaded files with proper MIME types"""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine MIME type based on file extension
    mime_type = "application/octet-stream"  # default
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        mime_type = f"image/{filename.split('.')[-1].lower()}"
    elif filename.lower().endswith('.pdf'):
        mime_type = "application/pdf"

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=filename
    )

@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation_endpoint(donation_id: UUID, db: Session = Depends(get_db)):
    """Get a specific donation"""
    try:
        db_donation = get_donation(db, donation_id)
        if not db_donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        return DonationResponse(
            id=db_donation.id,
            title=db_donation.title,
            donor_name=db_donation.donor_name,
            donor_email=db_donation.donor_email,
            donor_phone=db_donation.donor_phone,
            amount=db_donation.amount,
            is_anonymous=db_donation.is_anonymous,
            message=db_donation.message,
            status=db_donation.status,
            payment_reference=db_donation.payment_reference,
            created_at=db_donation.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving donation: {str(e)}")

@router.put("/{donation_id}", response_model=DonationResponse)
async def update_donation_endpoint(
    donation_id: UUID,
    donation_update: DonationUpdate,
    db: Session = Depends(get_db)
):
    """Update a donation"""
    try:
        db_donation = update_donation(db, donation_id, donation_update)
        if not db_donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        return DonationResponse(
            id=db_donation.id,
            title=db_donation.title,
            donor_name=db_donation.donor_name,
            donor_email=db_donation.donor_email,
            donor_phone=db_donation.donor_phone,
            amount=db_donation.amount,
            is_anonymous=db_donation.is_anonymous,
            message=db_donation.message,
            status=db_donation.status,
            payment_reference=db_donation.payment_reference,
            created_at=db_donation.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating donation: {str(e)}")

@router.delete("/{donation_id}")
async def delete_donation_endpoint(donation_id: UUID, db: Session = Depends(get_db)):
    """Delete a donation"""
    try:
        success = delete_donation(db, donation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Donation not found")

        return JSONResponse(
            status_code=200,
            content={"message": "Donation deleted successfully"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting donation: {str(e)}")

@router.get("/email/{email}")
async def get_donations_by_email_endpoint(
    email: str,
    db: Session = Depends(get_db)
):
    """Get all donations by donor email"""
    try:
        donations = get_donations_by_email(db, email)
        return {
            "donations": donations,
            "total": len(donations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving donations: {str(e)}")

@router.get("/stats/total")
async def get_donation_stats(
    db: Session = Depends(get_db),
    title: Optional[str] = Query(None, description="Filter by donation title")
):
    """Get donation statistics"""
    try:
        total_amount = get_total_donated_amount(db, title)
        total_count = count_donations(db, title)

        return {
            "total_amount": total_amount,
            "total_donations": total_count,
            "average_donation": total_amount / total_count if total_count > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")

@router.post("/{donation_id}/verify")
async def verify_donation(
    donation_id: UUID,
    db: Session = Depends(get_db)
):
    """Verify a donation (mark as completed)"""
    try:
        donation_update = DonationUpdate(status="completed")
        db_donation = update_donation(db, donation_id, donation_update)

        if not db_donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Donation verified successfully",
                "donation_id": str(donation_id),
                "status": "completed"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying donation: {str(e)}")

@router.post("/{donation_id}/reject")
async def reject_donation(
    donation_id: UUID,
    db: Session = Depends(get_db)
):
    """Reject a donation (mark as failed)"""
    try:
        donation_update = DonationUpdate(status="failed")
        db_donation = update_donation(db, donation_id, donation_update)

        if not db_donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Donation rejected",
                "donation_id": str(donation_id),
                "status": "failed"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting donation: {str(e)}")