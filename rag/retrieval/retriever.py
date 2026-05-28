from dataclasses import dataclass

from rag.config import Settings
from rag.ingestion.embedder import get_embedder
from rag.ingestion.store import ChromaStore

__all__ = ["RetrievedChunk", "retrieve"]


@dataclass
class RetrievedChunk:
    content: str
    score: float
    metadata: dict


def _distance_to_similarity(distance: float, space: str) -> float:
    """Convert ChromaDB distance to a comparable [0, 1] similarity score.

    Assumes embeddings are unit-normalized (OpenAI, Gemini,
    sentence-transformers all return normalized vectors by default).

    - ``cosine``  : distance = 1 - cos_sim  →  similarity = 1 - distance
    - ``ip``      : distance = cos_sim      →  similarity = distance
    - ``l2``      : distance = squared L2 between unit vectors
                              = 2 - 2*cos_sim
                              →  similarity = 1 - distance/2
    """
    if space == "cosine":
        return 1.0 - distance
    if space == "ip":
        return float(distance)
    # default: l2 (ChromaDB's default if the collection wasn't created
    # with an explicit hnsw:space metadata entry).
    return 1.0 - distance / 2.0


def retrieve(
    question: str,
    config: Settings,
    *,
    top_k: int | None = None,
    where: dict | None = None,
) -> list[RetrievedChunk]:
    if top_k is None:
        top_k = config.retrieval.top_k

    store = ChromaStore(config)
    embedder = get_embedder(config)

    query_embedding = embedder.embed_query(question)

    candidates = top_k * 2
    results = store.collection.query(
        query_embeddings=[query_embedding],
        n_results=candidates,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[RetrievedChunk] = []
    if not results["documents"] or not results["documents"][0]:
        return chunks

    metadata = store.collection.metadata or {}
    space = metadata.get("hnsw:space", "l2")

    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = _distance_to_similarity(distance, space)
        if score >= config.retrieval.score_threshold:
            chunks.append(RetrievedChunk(
                content=doc,
                score=score,
                metadata=meta,
            ))

    chunks.sort(key=lambda c: c.score, reverse=True)
    return chunks[:top_k]
