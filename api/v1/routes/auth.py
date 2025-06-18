from datetime import datetime, timedelta
from typing import Optional, Set
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, APIRouter, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import os

from api.v1.models.models import Admin, UserRole
from api.db.database import get_db
from api.utils.success_response import success_response

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.ADMIN

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

# Create router
router = APIRouter()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Simple in-memory token blacklist (for production, consider using Redis)
blacklisted_tokens: Set[str] = set()

# Utility Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": str(uuid.uuid4())  # JWT ID for token tracking
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": str(uuid.uuid4())  # JWT ID for token tracking
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode JWT token"""
    try:
        # Check if token is blacklisted
        if token in blacklisted_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type_claim: str = payload.get("type")
        
        # Validate token data
        if email is None or token_type_claim != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def create_token_response(user: Admin, include_refresh: bool = True) -> dict:
    """Create standardized token response"""
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
    }
    
    # Add refresh token if requested
    if include_refresh:
        refresh_token = create_refresh_token(
            data={"sub": user.email, "role": user.role.value, "user_id": str(user.id)}
        )
        response_data["refresh_token"] = refresh_token
    
    return response_data

# Dependencies
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Admin:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = verify_token(token, "access")
    email = payload.get("sub")
    
    # Get user from database
    user = db.query(Admin).filter(Admin.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated"
        )
    
    return user

def get_current_superadmin(current_user: Admin = Depends(get_current_user)) -> Admin:
    """Ensure current user is superadmin"""
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return current_user

def get_current_admin_or_superadmin(current_user: Admin = Depends(get_current_user)) -> Admin:
    """Ensure current user is admin or superadmin"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Authentication Routes - Simplified (No Refresh Token)
@router.post("/login", response_model=dict)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - returns only access token"""
    # Find user
    user = db.query(Admin).filter(Admin.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token response (access token only)
    token_data = create_token_response(user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Login successful",
        data=token_data
    )

@router.post("/register", response_model=dict)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_superadmin)
):
    """Register new admin - returns tokens for the new user"""
    # Check if user already exists
    existing_user = db.query(Admin).filter(Admin.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin
    hashed_password = get_password_hash(register_data.password)
    new_user = Admin(
        id=uuid.uuid4(),
        email=register_data.email,
        hashed_password=hashed_password,
        full_name=f"{register_data.first_name} {register_data.last_name}",
        role=register_data.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token response for the new user (access token only)
    token_data = create_token_response(new_user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Admin registered successfully",
        data=token_data
    )

@router.post("/logout", response_model=dict)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout user and invalidate tokens"""
    if credentials:
        # Add access token to blacklist
        blacklisted_tokens.add(credentials.credentials)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Successfully logged out"
    )

@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: Admin = Depends(get_current_user)):
    """Get current user information"""
    # Create fresh token for the response
    token_data = create_token_response(current_user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User information retrieved successfully",
        data=token_data
    )

@router.post("/verify-token", response_model=dict)
async def verify_user_token(current_user: Admin = Depends(get_current_user)):
    """Verify if token is valid and return fresh token"""
    # Create fresh token for the response
    token_data = create_token_response(current_user, include_refresh=False)
    token_data["valid"] = True
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Token is valid",
        data=token_data
    )

@router.post("/create-superadmin", response_model=dict)
async def create_superadmin(
    register_data: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Create the first superadmin - returns tokens"""
    # Check if any superadmin already exists
    existing_superadmin = db.query(Admin).filter(Admin.role == UserRole.SUPERADMIN).first()
    if existing_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin already exists. Use /register endpoint instead."
        )
    
    # Check if user already exists
    existing_user = db.query(Admin).filter(Admin.email == register_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create the superadmin
    hashed_password = get_password_hash(register_data.password)
    new_superadmin = Admin(
        id=uuid.uuid4(),
        email=register_data.email,
        hashed_password=hashed_password,
        full_name=f"{register_data.first_name} {register_data.last_name}",
        role=UserRole.SUPERADMIN,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(new_superadmin)
    db.commit()
    db.refresh(new_superadmin)
    
    # Create token response
    token_data = create_token_response(new_superadmin, include_refresh=True)
    
    # Set HTTP-only cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=token_data["refresh_token"],
        httponly=True,
        secure=False,  # Set to False for development (HTTP), True for production (HTTPS)
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Superadmin created successfully",
        data=token_data
    )

# Admin Management Routes (All return tokens in response)
@router.get("/admins", response_model=dict)
async def get_all_admins(
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_superadmin)
):
    """Get all admin users with fresh token"""
    admins = db.query(Admin).all()
    admin_list = [{
        "id": str(admin.id),
        "email": admin.email,
        "full_name": admin.full_name,
        "role": admin.role.value,
        "is_active": admin.is_active,
        "created_at": admin.created_at.isoformat()
    } for admin in admins]
    
    # Include fresh token in response
    token_data = create_token_response(current_user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Admins retrieved successfully",
        data={
            "admins": admin_list,
            **token_data
        }
    )

@router.patch("/admins/{admin_id}/toggle-status", response_model=dict)
async def toggle_admin_status(
    admin_id: str,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_superadmin)
):
    """Toggle admin active status with fresh token"""
    try:
        admin_uuid = uuid.UUID(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin ID format"
        )
    
    admin = db.query(Admin).filter(Admin.id == admin_uuid).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    if admin.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    admin.is_active = not admin.is_active
    db.commit()
    
    # Include fresh token in response
    token_data = create_token_response(current_user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message=f"Admin {'activated' if admin.is_active else 'deactivated'} successfully",
        data={
            "admin": {
                "id": str(admin.id),
                "email": admin.email,
                "is_active": admin.is_active
            },
            **token_data
        }
    )

@router.delete("/admins/{admin_id}", response_model=dict)
async def delete_admin(
    admin_id: str,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_superadmin)
):
    """Delete admin user with fresh token"""
    try:
        admin_uuid = uuid.UUID(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid admin ID format"
        )
    
    admin = db.query(Admin).filter(Admin.id == admin_uuid).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    if admin.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(admin)
    db.commit()
    
    # Include fresh token in response
    token_data = create_token_response(current_user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Admin deleted successfully",
        data=token_data
    )

# Utility route for token validation
@router.post("/validate-token", response_model=dict)
async def validate_token(current_user: Admin = Depends(get_current_user)):
    """Validate token and return user info with fresh token"""
    token_data = create_token_response(current_user, include_refresh=False)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Token validated successfully",
        data=token_data
    )