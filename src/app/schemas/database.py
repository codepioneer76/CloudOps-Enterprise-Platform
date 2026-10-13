"""Database subsystem schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatabaseBackendInfo(BaseModel):
    """Information regarding active relational database provider."""
    provider: str
    is_connected: bool
    database_name: str
    status: str
    description: str


class AuditRecordCreate(BaseModel):
    """Payload to insert an operational audit record."""
    event_type: str = Field(..., min_length=1, max_length=64, description="Action or event identifier")
    actor: str = Field(default="system", max_length=64, description="Actor or microservice initiator")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Metadata or event JSON body")


class AuditRecordDetail(BaseModel):
    """Stored audit log record."""
    id: int
    event_type: str
    actor: str
    payload: Dict[str, Any]
    created_at: str


class AuditRecordListResponse(BaseModel):
    """List response of audit log records."""
    count: int
    records: List[AuditRecordDetail]
