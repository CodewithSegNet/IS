# main.py with improved CORS configuration for cookie handling

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware 
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import os

from api.db.database import engine
from api.v1.models.models import Base
from api.v1.routes import (
    auth,
    admin,
    donations,
    users,
    newsletters,
    dashboard
)
from api.utils.settings import settings
from api.v1.routes import api_version_one

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PSF Admin Dashboard API",
    description="Backend API for Paul Smith Foundation Admin Dashboard",
    version="1.0.0"
)

# Request count middleware
request_counter = defaultdict(lambda: defaultdict(int))
class RequestCountMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        ip_address = request.client.host
        request_counter[endpoint][ip_address] += 1
        return await call_next(request)

# Improved CORS middleware configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",  
        "http://localhost:3000",   
        "http://127.0.0.1:3000",
        "https://paulsmithinitiatives.com",
        "https://www.paulsmithinitiatives.com"   
    ],
    allow_credentials=True,  # This is crucial for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(RequestCountMiddleware)

# Static and template directories
# email_templates = Jinja2Templates(directory='api/core/dependencies/email/templates')
# EMAIL_STATIC_DIR = 'api/core/dependencies/email/static'
# app.mount(f'/{EMAIL_STATIC_DIR}', StaticFiles(directory=EMAIL_STATIC_DIR), name='email-static')

MEDIA_DIR = './media'
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount('/media', StaticFiles(directory=MEDIA_DIR), name='media')

# Include versioned API routers
api_version_one.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_version_one.include_router(admin.router, prefix="/admin", tags=["Admin Management"])
api_version_one.include_router(donations.router, prefix="/donations", tags=["Donations"])
api_version_one.include_router(users.router, prefix="/users", tags=["Users"])
api_version_one.include_router(newsletters.router, prefix="/newsletters", tags=["Newsletters"])
api_version_one.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Register v1 API router
app.include_router(api_version_one)

# Root endpoints
@app.get("/")
async def root():
    return {"message": "PSF Admin Dashboard API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PSF Admin API"}

# Debug endpoint to check cookies (remove in production)
@app.get("/debug/cookies")
async def debug_cookies(request: Request):
    return {
        "cookies": dict(request.cookies),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None
    }

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)