"""Tests for system metrics and CloudOps architecture endpoints."""

from starlette.testclient import TestClient


def test_system_metrics(client: TestClient):
    """Verify runtime metrics are returned accurately."""
    response = client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "os_name" in data
    assert "python_version" in data
    assert data["pid"] > 0
    assert data["container_ready"] is True
    assert data["active_threads"] >= 1


def test_virtualization_comparison_architecture(client: TestClient):
    """Verify Module 1 Virtualization vs Containerization technical comparison."""
    response = client.get("/api/v1/system/architecture")
    assert response.status_code == 200
    data = response.json()
    assert "matrix" in data
    assert len(data["matrix"]) >= 5
    dimensions = [item["dimension"] for item in data["matrix"]]
    assert "Architecture Abstraction" in dimensions
    assert "Startup Time" in dimensions
    assert "Resource Overhead" in dimensions
    assert "Portability & Packaging" in dimensions
    assert "Security & Isolation" in dimensions


def test_cloudops_modules_overview(client: TestClient):
    """Verify all 8 Capstone modules are properly cataloged."""
    response = client.get("/api/v1/system/modules")
    assert response.status_code == 200
    data = response.json()
    assert data["total_modules"] == 8
    assert len(data["modules"]) == 8
    module_names = [m["module_name"] for m in data["modules"]]
    assert any("Virtualization" in name for name in module_names)
    assert any("Networking" in name for name in module_names)
    assert any("Serverless" in name for name in module_names)
    assert any("Security" in name for name in module_names)
    assert any("Infrastructure as Code" in name for name in module_names)
    assert any("CI/CD" in name for name in module_names)
    assert any("Big Data" in name for name in module_names)
    assert any("No-Code" in name for name in module_names)
