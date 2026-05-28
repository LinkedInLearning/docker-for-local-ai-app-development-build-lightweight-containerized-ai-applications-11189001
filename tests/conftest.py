"""Shared pytest fixtures for the RAG API test suite."""

import os

import pytest
from fastapi.testclient import TestClient


# Set before any module-level import of rag.api.main so _require_auth()
# returns False when the test process loads the app. Tests that exercise
# auth behaviour directly should use the autouse fixture below to restore
# a specific key set and use the `client` / `unauth_client` fixtures.
os.environ.setdefault("RAG_API_REQUIRE_AUTH", "false")


TEST_API_KEY = "test-key-1"


@pytest.fixture(autouse=True)
def _configure_test_env(monkeypatch):
    """Set RAG_API_KEYS and clear any cached value before each test."""
    monkeypatch.setenv("RAG_API_KEYS", TEST_API_KEY)
    monkeypatch.delenv("RAG_API_REQUIRE_AUTH", raising=False)

    # Bust the lru_cache so the new env value is picked up.
    from rag.api.dependencies import get_api_keys
    get_api_keys.cache_clear()
    yield
    get_api_keys.cache_clear()


@pytest.fixture
def client():
    """TestClient that auto-injects the test API key on every request."""
    from rag.api.main import app
    return TestClient(app, headers={"X-API-Key": TEST_API_KEY})


@pytest.fixture
def unauth_client():
    """TestClient WITHOUT an auth header — for negative tests."""
    from rag.api.main import app
    return TestClient(app)
