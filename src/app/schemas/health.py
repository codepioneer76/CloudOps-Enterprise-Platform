"""Health check schemas."""

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    """Schema for Kubernetes liveness probe."""
    status: Literal["live", "unhealthy"] = "live"
    timestamp: str = Field(..., description="ISO 8601 timestamp of probe")


class DependencyStatus(BaseModel):
    """Status of an individual subsystem or external dependency."""
    status: Literal["ok", "degraded", "unavailable"]
    connected: bool
    provider: str
    details: str


class ReadinessResponse(BaseModel):
    """Schema for Kubernetes readiness probe."""
    status: Literal["ready", "degraded", "not_ready"]
    timestamp: str
    dependencies: Dict[str, DependencyStatus]


class HealthSummaryResponse(BaseModel):
    """Overall health summary for monitoring and status dashboards."""
    app_name: str
    app_version: str
    app_env: str
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: str
    liveness: LivenessResponse
    readiness: ReadinessResponse
