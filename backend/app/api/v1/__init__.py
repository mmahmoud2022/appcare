"""
API routes
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, admin, doctor, patient, websocket

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router)

# Include admin routes
api_router.include_router(admin.router)

# Include doctor routes
api_router.include_router(doctor.router)

# Include patient routes
api_router.include_router(patient.router)

# Include WebSocket routes
api_router.include_router(websocket.router, tags=["websocket"])
