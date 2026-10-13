"""Storage subsystem schemas."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class StorageBackendInfo(BaseModel):
    """Information regarding active storage provider."""
    provider: str
    is_cloud_connected: bool = False
    status: str
    description: str


class BucketInfo(BaseModel):
    """Metadata for an object storage bucket or namespace."""
    name: str
    provider: str
    created_at: str
    object_count: int
    lifecycle_policy: Optional[str] = "Standard-IA / Glacier (Pending IaC)"


class StorageObjectMeta(BaseModel):
    """Metadata for a stored object."""
    key: str
    bucket: str
    size_bytes: int
    content_type: str = "text/plain"
    created_at: str
    etag: str
    metadata: Dict[str, str] = Field(default_factory=dict)


class StorageObjectCreate(BaseModel):
    """Payload to store an object."""
    key: str = Field(..., min_length=1, max_length=256, description="Object key/path")
    bucket: Optional[str] = Field(None, description="Target bucket. Defaults to primary bucket if omitted.")
    content_text: str = Field(..., description="String payload for the object")
    content_type: str = Field(default="text/plain", description="MIME content type")
    metadata: Dict[str, str] = Field(default_factory=dict)


class StorageObjectDetail(StorageObjectMeta):
    """Full detail of a stored object including payload."""
    content_text: str


class StorageListResponse(BaseModel):
    """Response containing list of stored objects."""
    bucket: str
    count: int
    objects: List[StorageObjectMeta]
