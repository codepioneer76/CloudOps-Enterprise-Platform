"""Tests for storage abstraction endpoints."""

from starlette.testclient import TestClient


def test_storage_info(client: TestClient):
    """Verify storage info reports provider without pretending cloud connection."""
    response = client.get("/api/v1/storage/info")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "in_memory_local_mock"
    assert data["is_cloud_connected"] is False
    assert "AWS S3 integration will be enabled" in data["description"]


def test_list_buckets(client: TestClient):
    """Verify list buckets endpoint."""
    response = client.get("/api/v1/storage/buckets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "test-bucket"


def test_put_get_list_delete_object_flow(client: TestClient):
    """Full lifecycle test: create, retrieve, list, and delete an object."""
    payload = {
        "key": "configs/app.yaml",
        "bucket": "test-bucket",
        "content_text": "server:\n  port: 8080\n",
        "content_type": "application/x-yaml",
        "metadata": {"environment": "test", "author": "devops"},
    }

    # 1. Store object
    put_res = client.post("/api/v1/storage/objects", json=payload)
    assert put_res.status_code == 201
    created_meta = put_res.json()
    assert created_meta["key"] == "configs/app.yaml"
    assert created_meta["bucket"] == "test-bucket"
    assert created_meta["size_bytes"] > 0
    assert "etag" in created_meta

    # 2. Retrieve object
    get_res = client.get("/api/v1/storage/objects/configs/app.yaml?bucket=test-bucket")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["key"] == "configs/app.yaml"
    assert detail["content_text"] == "server:\n  port: 8080\n"
    assert detail["metadata"]["environment"] == "test"

    # 3. List objects
    list_res = client.get("/api/v1/storage/objects?bucket=test-bucket")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["count"] == 1
    assert list_data["objects"][0]["key"] == "configs/app.yaml"

    # 4. Delete object
    del_res = client.delete("/api/v1/storage/objects/configs/app.yaml?bucket=test-bucket")
    assert del_res.status_code == 204

    # 5. Verify deletion - should return 404
    get_after_del = client.get("/api/v1/storage/objects/configs/app.yaml?bucket=test-bucket")
    assert get_after_del.status_code == 404


def test_storage_object_not_found(client: TestClient):
    """Verify 404 response when querying nonexistent object."""
    response = client.get("/api/v1/storage/objects/nonexistent.txt?bucket=test-bucket")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_storage_delete_nonexistent_returns_404(client: TestClient):
    """Verify 404 response when deleting nonexistent object."""
    response = client.delete("/api/v1/storage/objects/nonexistent.txt?bucket=test-bucket")
    assert response.status_code == 404


def test_storage_validation_error(client: TestClient):
    """Verify 422 error when required payload fields are missing."""
    invalid_payload = {"key": "test.txt"}  # missing content_text
    response = client.post("/api/v1/storage/objects", json=invalid_payload)
    assert response.status_code == 422
