"""API v1 root router aggregator."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.system import router as system_router
from app.api.v1.storage import router as storage_router
from app.api.v1.ml import router as ml_router
from app.api.v1.database import router as database_router

api_v1_router = APIRouter(prefix="/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(storage_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(database_router)
