"""
Vector Store service using ChromaDB + sentence-transformers.

Responsibilities:
  - Embed and store document chunks per project
  - Retrieve the most relevant chunks for a given query
"""
from __future__ import annotations

import uuid
from typing import Optional

import chromadb
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.core.config import settings

# ─── Singleton setup ──────────────────────────────────────────────────────────

_chroma_client: Optional[chromadb.PersistentClient] = None
_embedding_model: Optional[SentenceTransformer] = None

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"   # fast, 384-dim, runs on CPU


def _get_chroma() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
        )
        logger.info(f"ChromaDB client initialised at {settings.CHROMA_PERSIST_DIR}")
    return _chroma_client


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def _collection_name(project_id: str) -> str:
    """Each project gets its own ChromaDB collection."""
    # ChromaDB collection names must be alphanumeric + hyphens/underscores
    return f"project_{project_id.replace('-', '_')}"


# ─── Public API ───────────────────────────────────────────────────────────────

def add_chunks(project_id: str, chunks: list[str], source_filename: str) -> int:
    """
    Embed text chunks and store them in the project's ChromaDB collection.

    Returns the number of chunks stored.
    """
    if not chunks:
        return 0

    model = _get_embedding_model()
    embeddings = model.encode(chunks, show_progress_bar=False).tolist()

    client = _get_chroma()
    collection = client.get_or_create_collection(
        name=_collection_name(project_id),
        metadata={"hnsw:space": "cosine"},
    )

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": source_filename, "chunk_index": i} for i, _ in enumerate(chunks)]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(
        f"Stored {len(chunks)} chunks from '{source_filename}' "
        f"→ project '{project_id}'"
    )
    return len(chunks)


def retrieve_context(
    project_id: str,
    query: str,
    top_k: int = 6,
) -> list[str]:
    """
    Retrieve the top-k most relevant text chunks for a query.

    Returns a list of chunk strings (empty list if no documents have been uploaded).
    """
    client = _get_chroma()
    col_name = _collection_name(project_id)

    try:
        collection = client.get_collection(name=col_name)
    except Exception:
        logger.warning(
            f"No ChromaDB collection found for project '{project_id}'. "
            "No uploaded documents — context will be empty."
        )
        return []

    model = _get_embedding_model()
    query_embedding = model.encode([query], show_progress_bar=False).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count()),
        include=["documents"],
    )

    docs: list[str] = results.get("documents", [[]])[0]
    logger.debug(f"Retrieved {len(docs)} context chunks for project '{project_id}'")
    return docs


def delete_project_vectors(project_id: str) -> None:
    """Remove the entire vector collection for a project (e.g. on project deletion)."""
    client = _get_chroma()
    col_name = _collection_name(project_id)
    try:
        client.delete_collection(name=col_name)
        logger.info(f"Deleted vector collection for project '{project_id}'")
    except Exception:
        pass  # collection might not exist
