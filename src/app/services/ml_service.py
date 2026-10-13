"""Machine Learning service interface and baseline heuristic implementation."""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.schemas.ml import (
    MLBackendInfo,
    MLModelCatalogItem,
    MLPredictionResponse,
    WorkloadMetricsInput,
)


class MLService(ABC):
    """Abstract interface for CloudOps ML inference backends."""

    @abstractmethod
    def get_backend_info(self) -> MLBackendInfo:
        """Return provider and model connectivity metadata."""
        pass

    @abstractmethod
    def list_models(self) -> List[MLModelCatalogItem]:
        """List registered ML models in the catalog."""
        pass

    @abstractmethod
    def predict(self, metrics: WorkloadMetricsInput) -> MLPredictionResponse:
        """Run inference on workload metrics."""
        pass

    @abstractmethod
    def check_health(self) -> Tuple[bool, str]:
        """Verify ML subsystem health status."""
        pass


class LocalBaselineMLService(MLService):
    """
    Local heuristic baseline ML model for workload anomaly detection.
    Explicitly informs callers that cloud SageMaker/Vertex AI is not connected yet.
    """

    def __init__(self, model_version: str = "v1.0") -> None:
        self.model_version = model_version
        self.model_id = "cloudops-workload-anomaly-detector"

    def get_backend_info(self) -> MLBackendInfo:
        return MLBackendInfo(
            provider="local_baseline_heuristic",
            model_name="CloudOps Telemetry Anomaly Classifier",
            model_version=self.model_version,
            is_cloud_connected=False,
            task="workload_anomaly_detection",
            status="active_local_baseline",
            description="Local deterministic baseline classifier. AWS SageMaker / Vertex AI integration pending Module 7.",
        )

    def list_models(self) -> List[MLModelCatalogItem]:
        return [
            MLModelCatalogItem(
                model_id=self.model_id,
                name="CloudOps Workload Anomaly Classifier",
                task="workload_anomaly_detection",
                version=self.model_version,
                framework="Rule-based heuristic / scikit-learn baseline ready",
                status="deployed_local",
                cloud_integration_target="AWS SageMaker Endpoint / GCP Vertex AI",
            )
        ]

    def predict(self, metrics: WorkloadMetricsInput) -> MLPredictionResponse:
        t0 = time.perf_counter()

        # Deterministic evaluation logic
        cpu = metrics.cpu_utilization_pct
        mem = metrics.memory_utilization_pct
        err = metrics.error_rate_pct
        rps = metrics.request_rate_rps

        anomaly_detected = False
        if err > 10.0 or cpu > 90.0 or mem > 92.0:
            classification = "anomaly_critical"
            anomaly_detected = True
            confidence = 0.96
            action = "Immediate alert: trigger auto-scaling and investigate failing nodes."
        elif err > 3.0 or cpu > 75.0 or mem > 80.0:
            classification = "warning_high_load"
            anomaly_detected = False
            confidence = 0.88
            action = "Pre-emptive scaling: evaluate queue depth and pod replicas."
        elif rps == 0 and (cpu > 40.0 or mem > 50.0):
            classification = "anomaly_idle_drain"
            anomaly_detected = True
            confidence = 0.82
            action = "Investigate zombie processes or resource leak on idle service."
        else:
            classification = "normal"
            anomaly_detected = False
            confidence = 0.94
            action = "Nominal operation: metrics within standard threshold."

        latency_ms = round((time.perf_counter() - t0) * 1000, 3)
        now_iso = datetime.now(timezone.utc).isoformat()

        return MLPredictionResponse(
            classification=classification,
            anomaly_detected=anomaly_detected,
            confidence_score=confidence,
            recommended_action=action,
            inference_provider="local_baseline_heuristic",
            model_version=self.model_version,
            latency_ms=latency_ms,
            timestamp=now_iso,
        )

    def check_health(self) -> Tuple[bool, str]:
        # Baseline model is operational locally
        return True, "Baseline heuristic ML engine operational (SageMaker detached)"


_ml_instance: Optional[MLService] = None


def get_ml_service(model_version: str = "v1.0") -> MLService:
    """Singleton getter for ML service dependency injection."""
    global _ml_instance
    if _ml_instance is None:
        _ml_instance = LocalBaselineMLService(model_version=model_version)
    return _ml_instance
