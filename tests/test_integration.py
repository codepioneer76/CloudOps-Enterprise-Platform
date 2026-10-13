"""Integration tests for persistent storage, database connectivity, and failover."""

import pytest
from app.services.db_service import MockDatabaseService, PostgresDatabaseService
from app.services.storage_service import InMemoryStorageService, S3StorageService
from app.schemas.storage import StorageObjectDetail


def test_mock_database_lifecycle_and_persistence():
    """Verify database CRUD operations and in-session persistence."""
    db = MockDatabaseService()

    # Verify initial state
    assert len(db.list_records()) == 0

    # Insert multiple audit events
    rec1 = db.create_record(
        event_type="CONTAINER_INIT",
        actor="orchestrator",
        payload={"container": "cloudops-api", "version": "1.0.0"},
    )
    rec2 = db.create_record(
        event_type="CONFIG_APPLIED",
        actor="admin",
        payload={"storage": "minio", "db": "postgres"},
    )

    assert rec1.id == 1
    assert rec2.id == 2
    assert rec1.event_type == "CONTAINER_INIT"

    # Query records - should return in reverse chronological order
    records = db.list_records(limit=10)
    assert len(records) == 2
    assert records[0].id == 2
    assert records[1].id == 1
    assert records[0].payload["storage"] == "minio"


def test_in_memory_storage_persistence_and_isolation():
    """Verify storage CRUD operations and content integrity."""
    storage = InMemoryStorageService(default_bucket="integration-bucket")

    # Store object
    meta = storage.put_object(
        bucket="integration-bucket",
        key="manifests/deployment.json",
        content_text='{"replicas": 3, "strategy": "RollingUpdate"}',
        content_type="application/json",
        metadata={"managed_by": "terraform"},
    )
    assert meta.key == "manifests/deployment.json"
    assert meta.bucket == "integration-bucket"

    # Retrieve object
    obj = storage.get_object(bucket="integration-bucket", key="manifests/deployment.json")
    assert isinstance(obj, StorageObjectDetail)
    assert 'RollingUpdate' in obj.content_text
    assert obj.metadata["managed_by"] == "terraform"

    # List objects
    all_objs = storage.list_objects(bucket="integration-bucket")
    assert len(all_objs) == 1

    # Overwrite object and verify update
    storage.put_object(
        bucket="integration-bucket",
        key="manifests/deployment.json",
        content_text='{"replicas": 5, "strategy": "RollingUpdate"}',
        content_type="application/json",
    )
    updated_obj = storage.get_object(bucket="integration-bucket", key="manifests/deployment.json")
    assert '5' in updated_obj.content_text

    # Delete object
    assert storage.delete_object(bucket="integration-bucket", key="manifests/deployment.json") is True
    assert len(storage.list_objects(bucket="integration-bucket")) == 0


def test_postgres_service_connection_failure_reporting():
    """Verify PostgresDatabaseService reports unreachable status when host is offline."""
    db = PostgresDatabaseService(
        host="127.0.0.1",
        port=59999,  # Unused port
        dbname="test_fail",
        user="nobody",
        password="bad",
    )
    ok, msg = db.check_health()
    assert ok is False
    assert "failed" in msg.lower() or "connection" in msg.lower()

    info = db.get_backend_info()
    assert info.provider == "postgresql"
    assert info.is_connected is False
    assert info.status == "unreachable"


def test_live_postgres_container_connectivity_and_persistence():
    """Verify live connectivity and persistence against running Postgres container if active."""
    db = PostgresDatabaseService(
        host="127.0.0.1",
        port=5433,  # Docker Compose mapped port
        dbname="cloudops_db",
        user="cloudops_user",
        password="cloudops_secure_pass_local",
    )
    ok, msg = db.check_health()
    if not ok:
        pytest.skip(f"Live PostgreSQL container not reachable on port 5433: {msg}")

    # Insert test record into PostgreSQL container
    rec = db.create_record(
        event_type="PYTEST_INTEGRATION_VERIFIED",
        actor="pytest-runner",
        payload={"integration": "docker_compose_postgres", "volume": "cloudops_postgres_data"},
    )
    assert rec.id > 0
    assert rec.event_type == "PYTEST_INTEGRATION_VERIFIED"

    # Query back to verify record exists
    records = db.list_records(limit=10)
    assert any(r.event_type == "PYTEST_INTEGRATION_VERIFIED" for r in records)
