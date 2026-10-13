"""Tests for relational database subsystem endpoints."""

from starlette.testclient import TestClient


def test_database_info(client: TestClient):
    """Verify database info accurately reports mock state without pretending postgres connection."""
    response = client.get("/api/v1/database/info")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock_in_memory"
    assert data["is_connected"] is False
    assert "PostgreSQL" in data["description"]


def test_create_and_list_audit_records(client: TestClient):
    """Verify insertion and querying of operational audit records."""
    payload = {
        "event_type": "DEPLOY_START",
        "actor": "ci-pipeline",
        "payload": {"module": "Module 2", "version": "v1.0.0"},
    }

    # 1. Insert audit record
    post_res = client.post("/api/v1/database/records", json=payload)
    assert post_res.status_code == 201
    record = post_res.json()
    assert record["event_type"] == "DEPLOY_START"
    assert record["actor"] == "ci-pipeline"
    assert record["payload"]["module"] == "Module 2"
    assert "id" in record
    assert "created_at" in record

    # 2. List records
    list_res = client.get("/api/v1/database/records?limit=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["count"] >= 1
    assert list_data["records"][0]["event_type"] == "DEPLOY_START"


def test_create_record_validation_error(client: TestClient):
    """Verify validation error when required field is missing."""
    invalid_payload = {"actor": "ci-pipeline"}  # missing event_type
    response = client.post("/api/v1/database/records", json=invalid_payload)
    assert response.status_code == 422
