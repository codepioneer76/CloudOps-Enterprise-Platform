"""Tests for health, liveness, and readiness endpoints."""

from starlette.testclient import TestClient
from app.services.storage_service import StorageService, get_storage_service
from app.services.ml_service import MLService, get_ml_service
from app.main import create_app


def test_root_endpoint(client: TestClient):
    """Verify top-level root endpoint returns operational platform status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "app_name" in data
    assert data["docs"] == "/docs"


def test_liveness_probe(client: TestClient):
    """Verify Kubernetes liveness probe returns live status."""
    # Test top-level mount
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert "timestamp" in data

    # Test v1 mount
    response_v1 = client.get("/api/v1/health/live")
    assert response_v1.status_code == 200
    assert response_v1.json()["status"] == "live"


def test_readiness_probe_healthy(client: TestClient):
    """Verify Kubernetes readiness probe returns ready status and dependencies."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "dependencies" in data
    assert "storage" in data["dependencies"]
    assert "ml_inference" in data["dependencies"]

    # Verify we accurately report AWS/Cloud is detached
    storage_dep = data["dependencies"]["storage"]
    assert storage_dep["status"] == "ok"
    assert storage_dep["connected"] is False
    assert storage_dep["provider"] == "in_memory_local_mock"

    ml_dep = data["dependencies"]["ml_inference"]
    assert ml_dep["status"] == "ok"
    assert ml_dep["connected"] is False
    assert ml_dep["provider"] == "local_baseline_heuristic"


def test_health_summary(client: TestClient):
    """Verify full health summary endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["liveness"]["status"] == "live"
    assert data["readiness"]["status"] == "ready"


def test_readiness_probe_degraded_when_dependency_fails(test_settings, test_storage):
    """Verify readiness reports degraded when a subsystem fails."""
    class FailingMLService:
        def get_backend_info(self):
            from app.schemas.ml import MLBackendInfo
            return MLBackendInfo(
                provider="mock_failing",
                model_name="failed",
                model_version="0.0",
                is_cloud_connected=False,
                task="none",
                status="error",
                description="Failed",
            )
        def check_health(self):
            return False, "Simulated ML backend failure"

    app = create_app(custom_settings=test_settings)
    app.dependency_overrides[get_storage_service] = lambda: test_storage
    app.dependency_overrides[get_ml_service] = lambda: FailingMLService()

    with TestClient(app) as local_client:
        response = local_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["dependencies"]["ml_inference"]["status"] == "unavailable"
