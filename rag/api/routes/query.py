"""Query-side routes — the read half of the API.

Served by the lean query image. This module must never import the ingestion
router or the job runner, so it never pulls in the Docling parsing stack.
"""

from fastapi import APIRouter, HTTPException, Request, Response

from rag.api.dependencies import get_config, get_store
from rag.api.models import (
    ConfigResponse,
    DocumentInfo,
    QueryMetadataResponse,
    QueryRequest,
    QueryResponse,
    SanitizedErrorResponse,
    SourceResponse,
)
from rag.api.rate_limit import get_rate_limit_query, limiter
from rag.observability.logging import get_logger
from rag.retrieval.chain import query_rag

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        429: {
            "model": SanitizedErrorResponse,
            "description": "Rate limit exceeded",
        },
    },
)
@limiter.limit(get_rate_limit_query())
def query_documents(request: Request, body: QueryRequest, response: Response):
    """Synchronous query. Rate-limited per-IP via slowapi.

    `request: Request` MUST be the first non-self arg — slowapi's
    decorator introspects the function signature for it.

    `response: Response` is required when slowapi's
    `headers_enabled=True`: slowapi injects `X-RateLimit-Limit`,
    `X-RateLimit-Remaining`, `X-RateLimit-Reset` into it after a
    successful call. Without this parameter, slowapi raises
    "parameter `response` must be an instance of
    starlette.responses.Response".
    """
    config = get_config()

    try:
        response_obj = query_rag(
            question=body.question,
            config=config,
            top_k=body.top_k,
            rerank_method=body.rerank_method,
            chat_provider=body.chat_provider,
        )
    except ValueError as e:
        get_logger().warning(
            "query.invalid_input",
            extra={
                "stage": "query.invalid_input",
                "extra_data": {"error_type": type(e).__name__},
            },
        )
        raise HTTPException(status_code=400, detail="Invalid query parameters.")
    except Exception:
        # Sanitized via Phase 1 catch-all; preserves request_id.
        raise

    sources = [
        SourceResponse(
            file=s.file,
            page=s.page,
            section=s.section,
            excerpt=s.excerpt,
        )
        for s in response_obj.sources
    ]

    metadata = None
    if response_obj.metadata:
        metadata = QueryMetadataResponse(
            provider=response_obj.metadata.provider,
            model=response_obj.metadata.model,
            retrieval_count=response_obj.metadata.retrieval_count,
            latency_ms=response_obj.metadata.latency_ms,
        )

    return QueryResponse(
        answer=response_obj.answer,
        sources=sources,
        metadata=metadata,
    )


@router.get("/documents", response_model=list[DocumentInfo])
def list_documents():
    store = get_store()
    docs = store.list_documents()
    return [DocumentInfo(**doc) for doc in docs]


@router.get("/config", response_model=ConfigResponse)
def get_configuration():
    config = get_config()
    return ConfigResponse(
        active_embedding_provider=config.active.embedding_provider,
        active_chat_provider=config.active.chat_provider,
        chunking_method=config.chunking.method,
        chunk_size=config.chunking.chunk_size,
        retrieval_top_k=config.retrieval.top_k,
        rerank_enabled=config.retrieval.rerank,
        rerank_model=config.retrieval.rerank_model,
        chromadb_host=config.chromadb.host,
        chromadb_port=config.chromadb.port,
        collection_name=config.chromadb.collection_name,
        observability_enabled=config.observability.enabled,
    )
