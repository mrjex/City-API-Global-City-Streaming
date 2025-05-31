from fastapi import APIRouter
from core.globals import is_ready

router = APIRouter()

# Health check endpoint
@router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Readiness endpoint
@router.get("/ready")
async def ready_check():
    return {"ready": is_ready} 