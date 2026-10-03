import logging
from typing import Any, Dict, List, Optional

from src.rag.chunker import chunk_knowledge_records
from src.rag.embeddings import SparseVector, TFIDFEmbeddingEngine, cosine
from src.rag.loader import load_knowledge_documents

logger = logging.getLogger("vector_store")


class AgriculturalVectorStore:
    """Small in-memory TF-IDF vector store for the agricultural knowledge base."""

    def __init__(self):
        self.engine = TFIDFEmbeddingEngine()
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[List[SparseVector]] = None
        self.is_initialized = False

    def build_index(self) -> None:
        """Load, validate, chunk and index the agricultural knowledge base."""
        records = load_knowledge_documents()
        self.chunks = chunk_knowledge_records(records)

        if not self.chunks:
            logger.warning("No knowledge chunks found to index.")
            self.embeddings = None
            self.is_initialized = False
            return

        texts = [chunk.get("text", "") for chunk in self.chunks]
        try:
            self.embeddings = self.engine.fit_transform(texts)
        except ValueError as exc:
            logger.error("Unable to build TF-IDF index: %s", exc)
            self.embeddings = None
            self.is_initialized = False
            return

        if not self.embeddings:
            self.is_initialized = False
            return

        self.is_initialized = True
        logger.info("Vector store indexed %d knowledge chunks successfully.", len(self.chunks))

    def similarity_search(
        self,
        query: str,
        crop_filter: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return the most relevant knowledge chunks for a query."""
        if top_k <= 0:
            return []

        query = (query or "").strip()
        if not query:
            return []

        if not self.is_initialized or self.embeddings is None:
            self.build_index()
            if not self.is_initialized or self.embeddings is None:
                return []

        try:
            query_vector = self.engine.transform([query])[0]
            scores = [cosine(query_vector, doc) for doc in self.embeddings]
        except (ValueError, RuntimeError) as exc:
            logger.error("Vector similarity search failed: %s", exc)
            return []

        target_crop = (crop_filter or "").strip().casefold()
        results: List[Dict[str, Any]] = []

        for idx, raw_score in enumerate(scores):
            chunk = self.chunks[idx]
            score = float(raw_score)

            if target_crop:
                chunk_crop = str(chunk.get("crop", "")).strip().casefold()
                if target_crop not in chunk_crop and chunk_crop not in target_crop:
                    score *= 0.25

            if score <= 0.05:
                continue

            results.append({
                "score": round(score, 4),
                "chunk": chunk,
                "title": chunk.get("title", ""),
                "source": chunk.get("source", ""),
                "crop": chunk.get("crop", ""),
                "condition": chunk.get("condition", ""),
                "text": chunk.get("text", ""),
                "raw_record": chunk.get("raw_record", {}),
                "url": chunk.get("url", ""),
            })

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]
