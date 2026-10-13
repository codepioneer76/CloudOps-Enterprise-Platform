"""Top-level API router."""

from fastapi import APIRouter
from app.api.v1.router import api_v1_router

main_api_router = APIRouter(prefix="/api")
main_api_router.include_router(api_v1_router)
