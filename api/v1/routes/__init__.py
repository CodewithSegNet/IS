# api/v1/routes/__init__.py
from fastapi import APIRouter

# Create the main API router for version 1
api_version_one = APIRouter(prefix="/api/v1")

# This router will be used in main.py to include all v1 routes