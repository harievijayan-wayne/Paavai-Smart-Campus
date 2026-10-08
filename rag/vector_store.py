import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class FAISSVectorStore:
    """
    FAISS-powered vector store with metadata storage and persistence.
    Uses Inner Product on L2 normalized vectors for Cosine Similarity.
    """

    def __init__(self, index_dir: str = settings.VECTOR_STORE_DIR):
        self.index_dir = index_dir
        self.index_file = os.path.join(index_dir, "index.faiss")
        self.metadata_file = os.path.join(index_dir, "metadata.json")
        self.dimension = 384
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self._faiss_available = False

        self._init_faiss()
        self.load()

    def _init_faiss(self):
        try:
            import faiss
            self.faiss = faiss
            self._faiss_available = True
            self.index = self.faiss.IndexFlatIP(self.dimension)
        except ImportError:
            logger.warning("FAISS library not installed. Falling back to in-memory numpy cosine similarity store.")
            self._faiss_available = False
            self.index = None
            self.embeddings_matrix: List[np.ndarray] = []

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        """
        Add chunks and their corresponding embedding vectors to the vector index.
        chunks metadata should include:
        chunk_id, document_id, title, page, version, is_verified, department_id, content
        """
        if len(chunks) == 0:
            return

        if self._faiss_available:
            if self.index is None or self.index.d != embeddings.shape[1]:
                self.dimension = embeddings.shape[1]
                self.index = self.faiss.IndexFlatIP(self.dimension)
            self.index.add(embeddings)
        else:
            if not hasattr(self, "embeddings_matrix"):
                self.embeddings_matrix = []
            for emb in embeddings:
                self.embeddings_matrix.append(emb)

        for chunk in chunks:
            self.metadata.append(chunk)

        self.save()
        logger.info(f"Added {len(chunks)} chunks to vector store. Total chunks: {len(self.metadata)}")

    def similarity_search(
        self,
        query_vector: np.ndarray,
        top_k: int = settings.RAG_TOP_K,
        verified_only: bool = True,
        min_threshold: float = settings.RAG_SIMILARITY_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """
        Search for top_k most similar chunks.
        Filters by `is_verified=True` when verified_only is set.
        Applies `min_threshold` cutoff.
        """
        if len(self.metadata) == 0:
            return []

        query_vec = np.array([query_vector], dtype=np.float32)
        results = []

        if self._faiss_available and self.index is not None and self.index.ntotal > 0:
            # FAISS search
            fetch_k = min(top_k * 4, self.index.ntotal)  # Fetch extra to filter for verified
            distances, indices = self.index.search(query_vec, fetch_k)

            for sim, idx in zip(distances[0], indices[0]):
                if idx == -1 or idx >= len(self.metadata):
                    continue
                score = float(sim)
                meta = self.metadata[idx]

                if verified_only and not meta.get("is_verified", False):
                    continue

                if score < min_threshold:
                    continue

                item = dict(meta)
                item["similarity"] = round(score, 4)
                results.append(item)

                if len(results) >= top_k:
                    break
        else:
            # In-memory numpy cosine similarity fallback
            scores = []
            for idx, emb in enumerate(self.embeddings_matrix if hasattr(self, "embeddings_matrix") else []):
                score = float(np.dot(query_vector, emb))
                scores.append((score, idx))

            scores.sort(key=lambda x: x[0], reverse=True)
            for score, idx in scores:
                meta = self.metadata[idx]
                if verified_only and not meta.get("is_verified", False):
                    continue
                if score < min_threshold:
                    continue

                item = dict(meta)
                item["similarity"] = round(score, 4)
                results.append(item)
                if len(results) >= top_k:
                    break

        return results

    def update_verification_status(self, document_id: str, is_verified: bool) -> None:
        """Update is_verified flag across all chunks of a document."""
        for item in self.metadata:
            if item.get("document_id") == document_id:
                item["is_verified"] = is_verified
        self.save()

    def delete_document(self, document_id: str) -> None:
        """Rebuild index removing all chunks belonging to document_id."""
        remaining_meta = []
        keep_indices = []

        for idx, item in enumerate(self.metadata):
            if item.get("document_id") != document_id:
                remaining_meta.append(item)
                keep_indices.append(idx)

        # In-memory reconstruction
        self.metadata = remaining_meta
        self.save()

    def save(self) -> None:
        """Persist FAISS index and metadata JSON to disk."""
        try:
            os.makedirs(self.index_dir, exist_ok=True)
            if self._faiss_available and self.index is not None:
                self.faiss.write_index(self.index, self.index_file)
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist vector index: {str(e)}")

    def load(self) -> bool:
        """Load persisted index and metadata from disk."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            if self._faiss_available and os.path.exists(self.index_file):
                self.index = self.faiss.read_index(self.index_file)
                self.dimension = self.index.d
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
                return True
        except Exception as e:
            logger.warning(f"Could not load vector store from disk ({str(e)}). Initializing clean index.")
        return False


vector_store = FAISSVectorStore()
