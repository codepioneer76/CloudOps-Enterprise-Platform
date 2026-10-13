"""Tests for ML inference service endpoints."""

from starlette.testclient import TestClient


def test_ml_backend_info(client: TestClient):
    """Verify ML info accurately reports local baseline without pretending SageMaker connection."""
    response = client.get("/api/v1/ml/info")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "local_baseline_heuristic"
    assert data["is_cloud_connected"] is False
    assert data["task"] == "workload_anomaly_detection"
    assert "SageMaker" in data["description"]


def test_list_ml_models(client: TestClient):
    """Verify registered ML models are present in the catalog."""
    response = client.get("/api/v1/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    model = data[0]
    assert model["model_id"] == "cloudops-workload-anomaly-detector"
    assert model["task"] == "workload_anomaly_detection"
    assert "AWS SageMaker" in model["cloud_integration_target"]


def test_ml_predict_normal_workload(client: TestClient):
    """Verify normal telemetry produces nominal classification."""
    payload = {
        "cpu_utilization_pct": 35.5,
        "memory_utilization_pct": 42.0,
        "request_rate_rps": 120.0,
        "error_rate_pct": 0.05,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "normal"
    assert data["anomaly_detected"] is False
    assert data["confidence_score"] >= 0.8
    assert data["latency_ms"] >= 0.0


def test_ml_predict_critical_anomaly(client: TestClient):
    """Verify severe metric spikes trigger anomaly_critical."""
    payload = {
        "cpu_utilization_pct": 94.2,
        "memory_utilization_pct": 95.0,
        "request_rate_rps": 350.0,
        "error_rate_pct": 14.5,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "anomaly_critical"
    assert data["anomaly_detected"] is True
    assert "Immediate alert" in data["recommended_action"]


def test_ml_predict_warning_high_load(client: TestClient):
    """Verify elevated load triggers warning without full anomaly alert."""
    payload = {
        "cpu_utilization_pct": 78.0,
        "memory_utilization_pct": 82.0,
        "request_rate_rps": 200.0,
        "error_rate_pct": 1.0,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "warning_high_load"
    assert data["anomaly_detected"] is False


def test_ml_predict_idle_drain_anomaly(client: TestClient):
    """Verify zero traffic with unexpected CPU load triggers idle drain alert."""
    payload = {
        "cpu_utilization_pct": 55.0,
        "memory_utilization_pct": 60.0,
        "request_rate_rps": 0.0,
        "error_rate_pct": 0.0,
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "anomaly_idle_drain"
    assert data["anomaly_detected"] is True


def test_ml_predict_validation_error(client: TestClient):
    """Verify 422 error on out-of-range metrics (e.g. CPU > 100%)."""
    invalid_payload = {
        "cpu_utilization_pct": 150.0,  # invalid percentage
        "memory_utilization_pct": 50.0,
        "request_rate_rps": 10.0,
        "error_rate_pct": 0.0,
    }
    response = client.post("/api/v1/ml/predict", json=invalid_payload)
    assert response.status_code == 422
