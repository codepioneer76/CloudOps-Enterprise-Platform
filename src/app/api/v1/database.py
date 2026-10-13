"""Database subsystem API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.database import (
    AuditRecordCreate,
    AuditRecordDetail,
    AuditRecordListResponse,
    DatabaseBackendInfo,
)
from app.services.db_service import (
    DatabaseError,
    DatabaseService,
    get_db_service,
)

router = APIRouter(prefix="/database", tags=["Database Subsystem"])


@router.get(
    "/info",
    response_model=DatabaseBackendInfo,
    status_code=status.HTTP_200_OK,
    summary="Database Backend Status",
)
def get_database_info(
    db: DatabaseService = Depends(get_db_service),
) -> DatabaseBackendInfo:
    return db.get_backend_info()


@router.post(
    "/records",
    response_model=AuditRecordDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Insert Operational Audit Record",
)
def create_audit_record(
    payload: AuditRecordCreate,
    db: DatabaseService = Depends(get_db_service),
) -> AuditRecordDetail:
    try:
        return db.create_record(
            event_type=payload.event_type,
            actor=payload.actor,
            payload=payload.payload,
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/records",
    response_model=AuditRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Operational Audit Records",
)
def list_audit_records(
    limit: int = Query(50, ge=1, le=500, description="Maximum records to return"),
    db: DatabaseService = Depends(get_db_service),
) -> AuditRecordListResponse:
    try:
        records = db.list_records(limit=limit)
        return AuditRecordListResponse(count=len(records), records=records)
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
