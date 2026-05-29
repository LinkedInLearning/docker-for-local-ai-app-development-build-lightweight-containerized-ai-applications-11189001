# Test Index

This document tracks all tests created during development, organized by system component.

---

## Summary

| Component | Test File | Tests | Phase |
|-----------|-----------|-------|-------|
| Configuration System | `tests/test_config.py` | 15 | Phase 2 |
| Ingestion Pipeline | `tests/test_ingestion.py` | 15 | Phase 3 |
| Retrieval & Generation | `tests/test_retrieval.py` | 11 | Phase 4 |
| FastAPI Service (core endpoints) | `tests/test_api.py` | 16 | Phase 4 (API Tier 1) |
| Middleware (RequestID, Auth, Errors, Logging) | `tests/test_middleware.py` | 16 | Phase 4 (API Tier 1) |
| Async Job Endpoints (/ingest 202, polling, listing) | `tests/test_jobs.py` | 13 | Phase 4 (API Tier 1) |
| JobRegistry (unit + concurrency) | `tests/test_job_registry.py` | 20 | Phase 4 (API Tier 1) |
| Security (resolve_under, upload limits, rate limits, path hardening) | `tests/test_security.py` | 26 | Phase 4 (API Tier 1) |

**Total tests**: 132

---

## Configuration System

**File**: `tests/test_config.py`

| Test | Description | Validates |
|------|-------------|-----------|
| `test_load_config_from_yaml` | Loads config from YAML, verifies all providers present | YAML parsing, Pydantic model construction |
| `test_active_providers` | Checks active provider defaults match YAML | Active provider config |
| `test_get_embedding_provider` | Gets OpenAI embedding config, checks name + dimensions | Embedding provider retrieval |
| `test_get_chat_provider` | Gets OpenAI chat config, checks name + temperature | Chat provider retrieval |
| `test_switch_chat_provider` | Switches to Anthropic, verifies model name | Runtime provider switching |
| `test_chunking_defaults` | Verifies chunking defaults from YAML | Chunking config loading |
| `test_chunking_invalid_method` | Assigns invalid method, expects ValidationError | `validate_assignment=True` enforcement |
| `test_chromadb_config` | Checks host, port, collection name | ChromaDB config loading |
| `test_retrieval_config` | Checks top_k, rerank, score_threshold | Retrieval config loading |
| `test_resolve_api_key_success` | Sets env var, resolves key successfully | Env var resolution (happy path) |
| `test_resolve_api_key_missing` | Unsets env var, expects ValueError | Missing key detection |
| `test_resolve_api_key_placeholder` | Sets "key_is_missing" placeholder, expects ValueError | Placeholder detection |
| `test_invalid_provider_name` | Constructs Settings with nonexistent provider, expects ValidationError | Cross-field model_validator |
| `test_config_file_not_found` | Passes nonexistent path, expects FileNotFoundError | File-not-found handling |
| `test_embedding_provider_without_embedding_model` | Sets Anthropic as embedding provider (no embedding model), expects ValidationError | Missing model validation |

**Run command**:
```bash
pytest tests/test_config.py -v
```

---

## Ingestion Pipeline

**File**: `tests/test_ingestion.py`

| Test | Description | Validates |
|------|-------------|-----------|
| `TestPdfParser::test_parse_pdf_file_not_found` | Passes nonexistent path, expects FileNotFoundError | Error handling |
| `TestPdfParser::test_parse_pdf_returns_elements` | Parses a real PDF, checks elements returned | Docling integration (requires PDF + network) |
| `TestPdfParser::test_parse_pdf_element_structure` | Checks type, page, content fields on parsed elements | Element structure |
| `TestChunker::test_recursive_chunking` | Chunks sample elements with recursive method | Recursive chunker |
| `TestChunker::test_by_title_chunking` | Chunks with by_title method | By-title chunker |
| `TestChunker::test_semantic_chunking` | Chunks with semantic method | Semantic chunker |
| `TestChunker::test_tables_kept_intact` | Verifies tables are not split when keep_tables_intact=True | Table preservation |
| `TestChunker::test_invalid_method` | Passes invalid method, expects ValueError | Input validation |
| `TestChunker::test_chunk_metadata_preserved` | Checks page, section_title, type flow through chunking | Metadata propagation |
| `TestChromaStore::test_store_init` | Mocks ChromaDB client, verifies connection params | Store initialization |
| `TestChromaStore::test_store_upsert` | Mocks collection, verifies upsert called | Upsert operation |
| `TestChromaStore::test_store_query` | Mocks query results, verifies return format | Query operation |
| `TestChromaStore::test_store_ingest_chunks` | Mocks embedder + collection, ingests 2 chunks | End-to-end ingest |
| `TestHelpers::test_generate_id_deterministic` | Same input produces same ID | ID consistency |
| `TestHelpers::test_generate_id_unique` | Different input produces different IDs | ID uniqueness |

**Run command**:
```bash
pytest tests/test_ingestion.py -v
```

---

## Retrieval & Generation

**File**: `tests/test_retrieval.py`

| Test | Description | Validates |
|------|-------------|-----------|
| `TestRetriever::test_retrieve_returns_chunks` | Mocks embedder + ChromaDB, verifies chunks returned sorted by score | Basic retrieval |
| `TestRetriever::test_retrieve_filters_by_threshold` | Sets high threshold, verifies low-score chunks filtered out | Score threshold filtering |
| `TestRetriever::test_retrieve_empty_results` | Mocks empty ChromaDB response, verifies empty list returned | Empty result handling |
| `TestReranker::test_rerank_none_method` | Method="none", returns top_k without reranking | Passthrough mode |
| `TestReranker::test_rerank_empty_chunks` | Empty input, returns empty list | Edge case |
| `TestReranker::test_rerank_invalid_method` | Invalid method, expects ValueError | Input validation |
| `TestReranker::test_rerank_cross_encoder` | Mocks CrossEncoder model, verifies scoring + sorting + no mutation | Cross-encoder reranking |
| `TestChain::test_build_context` | Builds context string from chunks, verifies source references | Context formatting |
| `TestChain::test_extract_sources` | Extracts Source objects from chunks | Source extraction |
| `TestChain::test_query_rag_end_to_end` | Mocks retrieve + rerank + LLM, verifies full response structure | End-to-end query |
| `TestChain::test_query_rag_no_results` | No chunks retrieved, verifies "no information" response | Empty result path |

**Run command**:
```bash
pytest tests/test_retrieval.py -v
```

---

## FastAPI Service (core endpoints)

**File**: `tests/test_api.py` — Phase 4 (API Tier 1)

Tests the main FastAPI app endpoints using a TestClient without auth
(RAG_API_REQUIRE_AUTH=false at import time). Updated in Phase 4 to fix
ingest tests that previously used source_dir outside the allowed root
(now use `pdf/` with runner_stub, or a temp subdir inside pdf/).

| Test | Description | Validates |
|------|-------------|-----------|
| `TestHealthEndpoint::test_health_healthy` | Mocks store, checks status/chromadb/documents | /health happy path |
| `TestHealthEndpoint::test_health_disconnected` | Store raises, checks degraded status | /health error path |
| `TestIngestEndpoint::test_ingest_success` | POSTs to pdf/ with runner_stub -> 202 | 202 job envelope |
| `TestIngestEndpoint::test_ingest_missing_directory` | pdf/does_not_exist -> 404 | candidate_missing |
| `TestIngestEndpoint::test_ingest_path_traversal_rejected` | /etc -> 403 | outside_allowed_root |
| `TestIngestEndpoint::test_ingest_no_pdfs` | Empty subdir under pdf/ -> 404 | No PDF files detection |
| `TestQueryEndpoint::test_query_success` | Mocks query_rag, checks answer/sources/metadata | /query happy path |
| `TestQueryEndpoint::test_query_value_error` | query_rag raises ValueError -> 400 sanitized | /query error path |
| `TestQueryEndpoint::test_query_missing_question` | Missing question field -> 422 | Pydantic validation |
| `TestDocumentsEndpoint::test_list_documents` | Mocks list_documents, checks list | GET /documents |
| `TestDocumentsEndpoint::test_delete_document` | Mocks collection.get + delete_by_source | DELETE /documents/{file} |
| `TestDocumentsEndpoint::test_delete_document_not_found` | Empty ids -> 404 | Document not found |
| `TestConfigEndpoint::test_get_config` | Mocks config, checks all fields | GET /config |
| `TestJobsEndpoint::test_get_job_unknown_id_404` | Unknown job_id -> 404 with envelope | Job not found |
| `TestJobsEndpoint::test_get_jobs_list_default` | GET /ingest/jobs -> 200 list | Job listing |
| `TestJobsEndpoint::test_get_jobs_list_invalid_limit_400_or_422` | limit=0 or 501 -> 400/422 | Limit validation |

**Run command**:
```bash
pytest tests/test_api.py -v
```

---

## Middleware (RequestID, Auth, Error Sanitization, Logging)

**File**: `tests/test_middleware.py` — Phase 4 (API Tier 1)

Auth tests use a fresh `auth_app` fixture (auth ENABLED, independent of the
default app's import-time auth=off). Error sanitization uses
`raise_server_exceptions=False` for the 500 path.

| Test | Description | Validates |
|------|-------------|-----------|
| `TestRequestID::test_request_id_generated_when_absent` | No header -> 12-char hex generated | RequestIDMiddleware generation |
| `TestRequestID::test_request_id_echoed_when_present` | Supplied ID echoed back | RequestIDMiddleware echo |
| `TestRequestID::test_request_id_stripped` | Whitespace stripped before echo | strip() behavior |
| `TestRequestID::test_request_id_differs_across_requests` | Two requests get different IDs | UUID uniqueness |
| `TestAuthAllowlist::test_health_open_without_key` | /health -> 200 with no key | Allowlist pass-through |
| `TestAuthAllowlist::test_openapi_open_without_key` | /openapi.json -> 200 with no key | Allowlist pass-through |
| `TestAuthAllowlist::test_protected_route_401_without_key` | /config with no key -> 401 | Auth enforcement |
| `TestAuthAllowlist::test_protected_route_200_with_valid_key` | /config with valid key -> 200 | Auth success |
| `TestAuthAllowlist::test_invalid_key_401` | Wrong key -> 401 | Invalid key rejection |
| `TestAuthAllowlist::test_401_body_is_sanitized_envelope` | Body has {request_id, error} only | Error envelope shape |
| `TestAuthAllowlist::test_401_has_request_id_header` | X-Request-ID == body.request_id | Header/body consistency |
| `TestErrorSanitization::test_http_4xx_detail_preserved_as_error` | 404 detail passes through as error | 4xx detail preservation |
| `TestErrorSanitization::test_500_strips_internal_detail` | RuntimeError message absent from 500 body | 500 sanitization |
| `TestErrorSanitization::test_500_returns_generic_message` | 500 error == GENERIC_500_MESSAGE | Generic 500 message |
| `TestErrorSanitization::test_error_response_has_request_id_header_and_body_match` | Header/body request_id match on 404 | Consistent IDs |
| `TestLogCapture::test_auth_failure_logged` | Auth failure logs WARNING with stage=auth.missing_header | Structured logging |
| `TestLogCapture::test_request_id_present_on_log_record` | Log records carry request_id attribute | RequestIDLogFilter |

**Run command**:
```bash
pytest tests/test_middleware.py -v
```

---

## Async Job Endpoints

**File**: `tests/test_jobs.py` — Phase 4 (API Tier 1)

Background tasks run synchronously in TestClient, so terminal state is
immediately visible after POST /ingest. Runner's heavy deps are patched
via the `runner_stub` conftest fixture.

| Test | Description | Validates |
|------|-------------|-----------|
| `TestIngestSubmission::test_post_ingest_returns_202` | POST pdf/ -> 202 with envelope | 202 job contract |
| `TestIngestSubmission::test_post_ingest_location_header` | Location == poll_url | Location header |
| `TestIngestSubmission::test_post_ingest_echoes_request_id` | X-Request-ID == body.request_id | ID consistency |
| `TestIngestSubmission::test_post_ingest_request_id_honored` | Client-supplied ID reflected | Custom request ID |
| `TestJobPolling::test_job_reaches_completed` | GET job immediately after POST -> completed | Background task runs |
| `TestJobPolling::test_completed_job_has_result` | Result block has documents_ingested >= 1 | JobResult shape |
| `TestJobPolling::test_job_failed_path` | parse_pdf raises -> status==failed | Failure path |
| `TestJobPolling::test_failed_error_message_sanitized` | error_message has class name not raw text | Error sanitization |
| `TestJobPolling::test_unknown_job_404` | Unknown job_id -> 404 | Job not found |
| `TestJobPolling::test_unknown_job_404_envelope` | 404 body has restart hint | Error envelope |
| `TestJobListing::test_list_newest_first` | 3 jobs -> newest first in list | FIFO order |
| `TestJobListing::test_list_respects_limit` | ?limit=1 returns 1 even with 3 jobs | Limit honored |
| `TestJobListing::test_list_invalid_limit_400` | limit=0 or 501 -> 400 | Limit validation |

**Run command**:
```bash
pytest tests/test_jobs.py -v
```

---

## JobRegistry (unit + concurrency)

**File**: `tests/test_job_registry.py` — Phase 4 (API Tier 1)

Pure unit tests; no app or HTTP. Tests construct local JobRegistry instances.

| Test | Description | Validates |
|------|-------------|-----------|
| `TestJobRegistryUnit::test_create_returns_pending` | New record has status=PENDING | Create lifecycle |
| `TestJobRegistryUnit::test_create_stamps_created_at` | created_at is a tz-aware datetime | Timestamp stamping |
| `TestJobRegistryUnit::test_get_unknown_returns_none` | Unknown ID -> None | get() miss |
| `TestJobRegistryUnit::test_update_running_stamps_started_at` | RUNNING transition sets started_at | Transition stamping |
| `TestJobRegistryUnit::test_second_running_does_not_restamp_started_at` | Second RUNNING preserves started_at | Guard condition |
| `TestJobRegistryUnit::test_completed_stamps_finished_at` | COMPLETED sets finished_at | Terminal stamping |
| `TestJobRegistryUnit::test_failed_stamps_finished_at` | FAILED sets finished_at | Terminal stamping |
| `TestJobRegistryUnit::test_update_unknown_raises` | update on missing ID -> JobNotFoundError | Error on unknown |
| `TestJobRegistryUnit::test_explicit_started_at_wins` | Caller-supplied started_at preserved | Explicit override |
| `TestJobRegistryUnit::test_evicts_oldest_when_full` | 4th create evicts 1st (max_size=3) | FIFO eviction |
| `TestJobRegistryUnit::test_list_newest_first` | list() -> [C, B, A] order | Reversed insertion |
| `TestJobRegistryUnit::test_list_respects_limit` | list(limit=2) returns 2 newest | Limit honored |
| `TestJobRegistryUnit::test_list_limit_zero_empty` | list(limit=0) == [] | Zero limit |
| `TestJobRegistryUnit::test_from_env_default` | No env var -> DEFAULT_REGISTRY_SIZE | from_env default |
| `TestJobRegistryUnit::test_from_env_parses_int` | RAG_API_JOB_REGISTRY_SIZE=42 -> max_size 42 | from_env parsing |
| `TestJobRegistryUnit::test_from_env_rejects_non_int` | Non-integer env -> RuntimeError | Validation |
| `TestJobRegistryUnit::test_init_rejects_zero_max_size` | max_size=0 -> ValueError | Constructor guard |
| `TestJobRegistryConcurrency::test_concurrent_creates_no_lost_records` | 50x20 creates = 1000 unique IDs | RLock correctness |
| `TestJobRegistryConcurrency::test_concurrent_create_and_evict_consistent_len` | 500 creates, cap=50 -> len==50 | Eviction under load |
| `TestJobRegistryConcurrency::test_concurrent_update_reads_never_torn` | Writer + reader race -> no torn fields | model_copy atomicity |

**Run command**:
```bash
pytest tests/test_job_registry.py -v
```

---

## Security (resolve_under, upload limits, rate limits, path hardening)

**File**: `tests/test_security.py` — Phase 4 (API Tier 1)

Four sections: pure resolve_under unit tests, isolated MaxUploadSizeMiddleware
tests (100-byte cap fixture), integration 413 acceptance test, rate-limit
integration tests, and /ingest path-hardening integration tests.

| Test | Description | Validates |
|------|-------------|-----------|
| `TestResolveUnder::test_accepts_root_itself` | Root resolves to itself | Base case |
| `TestResolveUnder::test_accepts_descendant` | Sub-dir accepted | Happy path |
| `TestResolveUnder::test_rejects_absolute_outside` | /etc -> outside_allowed_root | Outside root |
| `TestResolveUnder::test_rejects_dotdot_escape` | ../outside -> outside_allowed_root | Dotdot normalization |
| `TestResolveUnder::test_rejects_symlink_escape` | Symlink pointing outside root -> symlink_escapes_root | Symlink safety |
| `TestResolveUnder::test_accepts_symlink_within` | Symlink within root -> accepted | Internal symlink |
| `TestResolveUnder::test_missing_candidate_reason` | Non-existent path -> candidate_missing | Missing path |
| `TestResolveUnder::test_missing_root_reason` | Non-existent root -> allowed_root_missing | Missing root |
| `TestResolveUnder::test_returns_realpath` | Returned path is realpath (symlink resolved) | Return value |
| `TestUploadLimitMiddleware::test_413_on_oversize_content_length` | >100-byte body -> 413 | Middleware enforcement |
| `TestUploadLimitMiddleware::test_413_envelope_and_request_id` | 413 body + header consistency | Error envelope |
| `TestUploadLimitMiddleware::test_411_when_content_length_missing` | Chunked body -> 411 | Missing Content-Length |
| `TestUploadLimitMiddleware::test_400_on_invalid_content_length` | Non-numeric CL -> 400 | Invalid header |
| `TestUploadLimitMiddleware::test_within_limit_passes_through` | Small body -> 200 | Pass-through |
| `TestUploadLimitMiddleware::test_query_route_not_guarded` | /query large body -> 200 | Path exclusion |
| `TestUploadLimitIntegration::test_ingest_413_before_disk_write` | Spoofed 60MB CL on real app -> 413 | Acceptance criterion |
| `TestRateLimit::test_ingest_429_at_threshold` | 5 ok, 6th -> 429 | Rate threshold |
| `TestRateLimit::test_429_envelope_shape` | 429 body {request_id, error} | Error envelope |
| `TestRateLimit::test_429_has_retry_after_header` | Retry-After is non-negative integer | RFC compliance |
| `TestRateLimit::test_429_has_request_id_header` | X-Request-ID == body.request_id | Header consistency |
| `TestRateLimit::test_health_not_rate_limited` | 20 GETs to /health -> all 200 | No limit on health |
| `TestIngestPathHardening::test_path_outside_allowed_403` | /etc -> 403 | Outside root |
| `TestIngestPathHardening::test_path_dotdot_escape_to_existing_outside_403` | pdf/../docs -> 403 | Dotdot to existing |
| `TestIngestPathHardening::test_path_dotdot_to_missing_404` | pdf/../nonexistent -> 404 | Dotdot to missing |
| `TestIngestPathHardening::test_path_missing_404` | pdf/nonexistent -> 404 | Missing path |
| `TestIngestPathHardening::test_empty_dir_no_pdfs_404` | Empty dir under pdf/ -> 404 | No PDFs |
| `TestIngestPathHardening::test_valid_pdf_dir_202` | pdf/ with runner_stub -> 202 | Happy path |

**Run command**:
```bash
pytest tests/test_security.py -v
```

---

## Run All Tests

```bash
pytest tests/ -v
```

To run only the Phase 4 (API Tier 1) tests:

```bash
pytest tests/test_api.py tests/test_middleware.py tests/test_jobs.py tests/test_job_registry.py tests/test_security.py -v
```
