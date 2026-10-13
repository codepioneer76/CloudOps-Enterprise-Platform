"""Object storage abstraction endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.storage import (
    BucketInfo,
    StorageBackendInfo,
    StorageListResponse,
    StorageObjectCreate,
    StorageObjectDetail,
    StorageObjectMeta,
)
from app.services.storage_service import (
    ObjectNotFoundError,
    StorageError,
    StorageService,
    get_storage_service,
)

router = APIRouter(prefix="/storage", tags=["Storage Subsystem"])


@router.get(
    "/info",
    response_model=StorageBackendInfo,
    status_code=status.HTTP_200_OK,
    summary="Storage Backend Status",
)
def get_storage_info(
    storage: StorageService = Depends(get_storage_service),
) -> StorageBackendInfo:
    return storage.get_backend_info()


@router.get(
    "/buckets",
    response_model=List[BucketInfo],
    status_code=status.HTTP_200_OK,
    summary="List Storage Buckets",
)
def list_buckets(
    storage: StorageService = Depends(get_storage_service),
) -> List[BucketInfo]:
    return storage.list_buckets()


@router.get(
    "/objects",
    response_model=StorageListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Stored Objects",
)
def list_objects(
    bucket: Optional[str] = Query(None, description="Bucket name"),
    storage: StorageService = Depends(get_storage_service),
) -> StorageListResponse:
    target_bucket = bucket or "cloudops-artifacts"
    items = storage.list_objects(bucket=target_bucket)
    return StorageListResponse(
        bucket=target_bucket,
        count=len(items),
        objects=items,
    )


@router.post(
    "/objects",
    response_model=StorageObjectMeta,
    status_code=status.HTTP_201_CREATED,
    summary="Store / Upload Object",
)
def create_object(
    payload: StorageObjectCreate,
    storage: StorageService = Depends(get_storage_service),
) -> StorageObjectMeta:
    try:
        return storage.put_object(
            bucket=payload.bucket or "cloudops-artifacts",
            key=payload.key,
            content_text=payload.content_text,
            content_type=payload.content_type,
            metadata=payload.metadata,
        )
    except StorageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/objects/{key:path}",
    response_model=StorageObjectDetail,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Stored Object",
)
def get_object(
    key: str,
    bucket: Optional[str] = Query(None, description="Bucket name"),
    storage: StorageService = Depends(get_storage_service),
) -> StorageObjectDetail:
    target_bucket = bucket or "cloudops-artifacts"
    try:
        return storage.get_object(bucket=target_bucket, key=key)
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/objects/{key:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Stored Object",
)
def delete_object(
    key: str,
    bucket: Optional[str] = Query(None, description="Bucket name"),
    storage: StorageService = Depends(get_storage_service),
):
    target_bucket = bucket or "cloudops-artifacts"
    try:
        storage.delete_object(bucket=target_bucket, key=key)
        return None
    except ObjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
