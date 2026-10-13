"""Health endpoints for container orchestration and uptime monitoring."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.schemas.health import (
    DependencyStatus,
    HealthSummaryResponse,
    LivenessResponse,
    ReadinessResponse,
)
from app.services.storage_service import StorageService, get_storage_service
from app.services.ml_service import MLService, get_ml_service
from app.services.db_service import DatabaseService, get_db_service

router = APIRouter(prefix="/health", tags=["Health & Monitoring"])


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Kubernetes Liveness Probe",
    description="Indicates whether the application container is running and healthy.",
)
def get_liveness() -> LivenessResponse:
    return LivenessResponse(
        status="live",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Kubernetes Readiness Probe",
    description="Verifies subsystem readiness before routing traffic to the container.",
)
def get_readiness(
    storage: StorageService = Depends(get_storage_service),
    ml: MLService = Depends(get_ml_service),
    db: DatabaseService = Depends(get_db_service),
) -> ReadinessResponse:
    storage_ok, storage_detail = storage.check_health()
    ml_ok, ml_detail = ml.check_health()
    db_ok, db_detail = db.check_health()

    dependencies = {
        "storage": DependencyStatus(
            status="ok" if storage_ok else "unavailable",
            connected=storage.get_backend_info().is_cloud_connected,
            provider=storage.get_backend_info().provider,
            details=storage_detail,
        ),
        "ml_inference": DependencyStatus(
            status="ok" if ml_ok else "unavailable",
            connected=ml.get_backend_info().is_cloud_connected,
            provider=ml.get_backend_info().provider,
            details=ml_detail,
        ),
        "database": DependencyStatus(
            status="ok" if db_ok else "unavailable",
            connected=db.get_backend_info().is_connected,
            provider=db.get_backend_info().provider,
            details=db_detail,
        ),
    }

    all_ready = storage_ok and ml_ok and db_ok
    readiness_status = "ready" if all_ready else "degraded"

    return ReadinessResponse(
        status=readiness_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        dependencies=dependencies,
    )


@router.get(
    "",
    response_model=HealthSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Summary",
    description="Provides consolidated liveness and readiness diagnostic report.",
)
def get_health_summary(
    settings: Settings = Depends(get_settings),
    storage: StorageService = Depends(get_storage_service),
    ml: MLService = Depends(get_ml_service),
    db: DatabaseService = Depends(get_db_service),
) -> HealthSummaryResponse:
    liveness = get_liveness()
    readiness = get_readiness(storage=storage, ml=ml, db=db)

    overall_status = "healthy" if readiness.status == "ready" else "degraded"

    return HealthSummaryResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        app_env=settings.app_env,
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        liveness=liveness,
        readiness=readiness,
    )
