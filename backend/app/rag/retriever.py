"""
ChromaDB-based retriever for legal document search with metadata filtering.

Supports filtering by state, section, and topic. Uses a two-pass strategy:
first retrieves state-specific results, then supplements with central/general
results to ensure comprehensive coverage.
"""
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.rag.embeddings import get_embedding_function
from app.core.logging import get_logger

logger = get_logger(__name__)

LEGAL_COLLECTION = "legal_corpus"


def get_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


class LegalRetriever:
    def __init__(self, top_k: int = 10):
        self.top_k = top_k
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(name=LEGAL_COLLECTION)
        self.embedding_fn = get_embedding_function()

    def retrieve(
        self,
        query: str,
        state: Optional[str] = None,
        section: Optional[str] = None,
        topic: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        k = top_k or self.top_k
        query_embedding = self.embedding_fn.embed_query(query)

        where_filter = self._build_filter(state=state, section=section, topic=topic)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        seen_contents = set()
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                content_hash = hash(doc[:200])
                if content_hash in seen_contents:
                    continue
                seen_contents.add(content_hash)
                retrieved.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        if state and state != "central" and len(retrieved) < k:
            central_filter = self._build_filter(state="central", section=section, topic=topic)
            supplement_k = k - len(retrieved)
            central_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=supplement_k,
                where=central_filter if central_filter else None,
                include=["documents", "metadatas", "distances"],
            )
            if central_results and central_results["documents"]:
                for i, doc in enumerate(central_results["documents"][0]):
                    content_hash = hash(doc[:200])
                    if content_hash in seen_contents:
                        continue
                    seen_contents.add(content_hash)
                    retrieved.append({
                        "content": doc,
                        "metadata": central_results["metadatas"][0][i] if central_results["metadatas"] else {},
                        "distance": central_results["distances"][0][i] if central_results["distances"] else None,
                    })

        logger.info(f"Retrieved {len(retrieved)} chunks for query: {query[:80]}...")
        return retrieved

    def _build_filter(
        self,
        state: Optional[str] = None,
        section: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> Optional[Dict]:
        conditions = []
        if state:
            if state.startswith("multi_state"):
                conditions.append({"state": state})
            else:
                conditions.append({"$or": [{"state": state}, {"state": "central"}]})
        if section:
            conditions.append({"section": section})
        if topic:
            conditions.append({"topic": topic})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}
