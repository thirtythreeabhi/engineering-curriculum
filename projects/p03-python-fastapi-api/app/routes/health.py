"""Health check and readiness probes."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "catalog-api"}


@router.get("/ready")
async def readiness_probe():
    return {"ready": True}
