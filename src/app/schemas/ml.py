"""Machine Learning and AI inference schemas."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class MLBackendInfo(BaseModel):
    """Information regarding active ML inference provider."""
    provider: str
    model_name: str
    model_version: str
    is_cloud_connected: bool = False
    task: str
    status: str
    description: str


class WorkloadMetricsInput(BaseModel):
    """Workload telemetry metrics to evaluate."""
    cpu_utilization_pct: float = Field(..., ge=0.0, le=100.0, description="CPU usage %")
    memory_utilization_pct: float = Field(..., ge=0.0, le=100.0, description="Memory usage %")
    request_rate_rps: float = Field(..., ge=0.0, description="Requests per second")
    error_rate_pct: float = Field(..., ge=0.0, le=100.0, description="Error rate %")
    extra_features: Dict[str, float] = Field(default_factory=dict)


class MLPredictionResponse(BaseModel):
    """Inference result from ML inference service."""
    classification: str = Field(..., description="E.g., normal, warning_high_load, anomaly_critical")
    anomaly_detected: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    recommended_action: str
    inference_provider: str
    model_version: str
    latency_ms: float
    timestamp: str


class MLModelCatalogItem(BaseModel):
    """Catalog metadata for registered ML models."""
    model_id: str
    name: str
    task: str
    version: str
    framework: str
    status: str
    cloud_integration_target: str
