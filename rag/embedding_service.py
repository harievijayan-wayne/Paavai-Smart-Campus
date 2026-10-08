from typing import List
import numpy as np
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    """
    Generates dense embeddings using configurable Hugging Face Sentence Transformers.
    Embeddings are L2 normalized to allow fast Inner Product (IP) cosine similarity in FAISS.
    """

    def __init__(self):
        self.model_name = settings.HF_EMBEDDING_MODEL
        self._model = None
        self._dimension = 384  # Standard dimension for all-MiniLM-L6-v2

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                # Infer actual dimension
                test_emb = self._model.encode(["test"])
                self._dimension = test_emb.shape[1]
                logger.info(f"Embedding model loaded. Dimension: {self._dimension}")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({str(e)}). Using deterministic fallback embeddings.")
                self._model = "fallback"
        return self._model

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed a list of text strings into normalized float32 vectors."""
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)

        model = self._get_model()
        if model != "fallback":
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings.astype(np.float32)
        else:
            return self._fallback_embed(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string into a normalized float32 vector."""
        return self.embed_documents([query])[0]

    def _fallback_embed(self, texts: List[str]) -> np.ndarray:
        """Deterministic pseudo-embedding for testing or when torch is unavailable."""
        vectors = []
        for text in texts:
            np.random.seed(abs(hash(text)) % (2**32))
            vec = np.random.randn(self._dimension).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)


embedding_service = EmbeddingService()
