"""Pytest fixtures for CloudOps Enterprise Platform tests."""

import pytest
from starlette.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.storage_service import InMemoryStorageService, get_storage_service
from app.services.ml_service import LocalBaselineMLService, get_ml_service
from app.services.db_service import MockDatabaseService, get_db_service


@pytest.fixture
def test_settings() -> Settings:
    """Return test settings instance."""
    return Settings(
        app_name="CloudOps Enterprise Platform (Test)",
        app_env="testing",
        debug=True,
    )


@pytest.fixture
def test_storage() -> InMemoryStorageService:
    """Return isolated storage service for testing."""
    return InMemoryStorageService(default_bucket="test-bucket")


@pytest.fixture
def test_ml() -> LocalBaselineMLService:
    """Return baseline ML service for testing."""
    return LocalBaselineMLService(model_version="test-v1.0")


@pytest.fixture
def test_db() -> MockDatabaseService:
    """Return isolated mock database service for testing."""
    return MockDatabaseService()


@pytest.fixture
def client(test_settings, test_storage, test_ml, test_db) -> TestClient:
    """Return test client with dependency overrides."""
    app = create_app(custom_settings=test_settings)
    app.dependency_overrides[get_storage_service] = lambda: test_storage
    app.dependency_overrides[get_ml_service] = lambda: test_ml
    app.dependency_overrides[get_db_service] = lambda: test_db

    with TestClient(app) as test_client:
        yield test_client
