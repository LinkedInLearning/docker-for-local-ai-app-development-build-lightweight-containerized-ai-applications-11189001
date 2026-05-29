from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rag.api.main import app
from rag.config import (
    ActiveConfig,
    ChromaDBConfig,
    ChunkingConfig,
    ModelConfig,
    ModelsConfig,
    ObservabilityConfig,
    ProviderConfig,
    RetrievalConfig,
    Settings,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_config():
    return Settings(
        providers={
            "openai": ProviderConfig(
                api_key_env="OPENAI_API_KEY",
                models=ModelsConfig(
                    embedding=ModelConfig(
                        name="text-embedding-3-small",
                        dimensions=1536,
                    ),
                    chat=ModelConfig(
                        name="gpt-4o",
                        temperature=0.0,
                        max_tokens=2048,
                    ),
                ),
            ),
        },
        active=ActiveConfig(
            embedding_provider="openai",
            chat_provider="openai",
        ),
        chunking=ChunkingConfig(),
        retrieval=RetrievalConfig(),
        chromadb=ChromaDBConfig(),
        observability=ObservabilityConfig(),
    )


class TestHealthEndpoint:
    @patch("rag.api.main.get_store")
    @patch("rag.api.main.get_config")
    def test_health_healthy(
        self, mock_config_fn, mock_store_fn, client, mock_config
    ):
        mock_config_fn.return_value = mock_config
        mock_store = MagicMock()
        mock_store.count.return_value = 42
        mock_store_fn.return_value = mock_store

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["chromadb"] == "connected"
        assert data["documents"] == 42

    @patch("rag.api.main.get_store")
    @patch("rag.api.main.get_config")
    def test_health_disconnected(
        self, mock_config_fn, mock_store_fn, client, mock_config
    ):
        mock_config_fn.return_value = mock_config
        mock_store_fn.side_effect = Exception("Connection refused")

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["chromadb"] == "disconnected"


class TestIngestEndpoint:
    def test_ingest_success(self, client, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        with patch("rag.api.main.Path.cwd", return_value=tmp_path.parent):
            response = client.post("/ingest", json={
                "source_dir": str(tmp_path),
                "chunking_method": "recursive",
            })
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "poll_url" in data
        assert data["poll_url"] == f"/ingest/jobs/{data['job_id']}"
        assert response.headers["Location"] == data["poll_url"]
        assert "request_id" in data and data["request_id"]
        assert response.headers["X-Request-ID"] == data["request_id"]

    def test_ingest_missing_directory(self, client, tmp_path):
        missing = tmp_path / "does_not_exist"
        with patch("rag.api.main.Path.cwd",
                   return_value=tmp_path):
            response = client.post("/ingest", json={
                "source_dir": str(missing),
            })
        assert response.status_code == 404

    def test_ingest_path_traversal_rejected(self, client):
        response = client.post("/ingest", json={
            "source_dir": "../../etc",
        })
        assert response.status_code == 403

    def test_ingest_no_pdfs(self, client, tmp_path):
        with patch("rag.api.main.Path.cwd",
                   return_value=tmp_path.parent):
            response = client.post("/ingest", json={
                "source_dir": str(tmp_path),
            })
        assert response.status_code == 404
        assert "No PDF files" in response.json()["error"]


class TestQueryEndpoint:
    @patch("rag.api.main.get_config")
    @patch("rag.api.main.query_rag")
    def test_query_success(
        self, mock_query_rag, mock_config_fn, client, mock_config
    ):
        mock_config_fn.return_value = mock_config

        mock_response = MagicMock()
        mock_response.answer = "Revenue was $50B"
        mock_response.sources = [MagicMock(
            file="10Q.pdf", page=5,
            section="Revenue", excerpt="Revenue..."
        )]
        mock_response.metadata = MagicMock(
            provider="openai", model="gpt-4o",
            retrieval_count=3, latency_ms=1200
        )
        mock_query_rag.return_value = mock_response

        response = client.post("/query", json={
            "question": "What was the revenue?",
        })
        assert response.status_code == 200
        data = response.json()
        assert "50B" in data["answer"]
        assert len(data["sources"]) == 1
        assert data["metadata"]["provider"] == "openai"

    @patch("rag.api.main.get_config")
    @patch("rag.api.main.query_rag")
    def test_query_value_error(
        self, mock_query_rag, mock_config_fn, client, mock_config
    ):
        mock_config_fn.return_value = mock_config
        mock_query_rag.side_effect = ValueError("Invalid provider")

        response = client.post("/query", json={
            "question": "test",
        })
        assert response.status_code == 400
        assert response.json()["error"] == "Invalid query parameters."

    def test_query_missing_question(self, client):
        response = client.post("/query", json={})
        assert response.status_code == 422


class TestDocumentsEndpoint:
    @patch("rag.api.main.get_store")
    def test_list_documents(self, mock_store_fn, client):
        mock_store = MagicMock()
        mock_store.list_documents.return_value = [
            {"file": "10Q-Q1.pdf", "chunks": 45},
            {"file": "10Q-Q2.pdf", "chunks": 52},
        ]
        mock_store_fn.return_value = mock_store

        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["file"] == "10Q-Q1.pdf"

    @patch("rag.api.main.get_store")
    def test_delete_document(self, mock_store_fn, client):
        mock_store = MagicMock()
        mock_store.collection.get.return_value = {
            "ids": ["chunk-1", "chunk-2"]
        }
        mock_store_fn.return_value = mock_store

        response = client.delete("/documents/10Q-Q1.pdf")
        assert response.status_code == 200
        mock_store.delete_by_source.assert_called_once_with(
            "10Q-Q1.pdf"
        )

    @patch("rag.api.main.get_store")
    def test_delete_document_not_found(self, mock_store_fn, client):
        mock_store = MagicMock()
        mock_store.collection.get.return_value = {"ids": []}
        mock_store_fn.return_value = mock_store

        response = client.delete("/documents/nonexistent.pdf")
        assert response.status_code == 404


class TestConfigEndpoint:
    @patch("rag.api.main.get_config")
    def test_get_config(self, mock_config_fn, client, mock_config):
        mock_config_fn.return_value = mock_config

        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert data["active_chat_provider"] == "openai"
        assert data["chunking_method"] == "recursive"
        assert data["chromadb_host"] == "chromadb"
        assert data["rerank_enabled"] is True


class TestJobsEndpoint:
    def test_get_job_unknown_id_404(self, client):
        response = client.get("/ingest/jobs/does-not-exist")
        assert response.status_code == 404
        data = response.json()
        assert "request_id" in data and data["request_id"]
        assert "error" in data

    def test_get_jobs_list_default(self, client):
        response = client.get("/ingest/jobs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_jobs_list_invalid_limit_400_or_422(self, client):
        for bad_limit in ("0", "501"):
            response = client.get(f"/ingest/jobs?limit={bad_limit}")
            assert response.status_code in (400, 422)
