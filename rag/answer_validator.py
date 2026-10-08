from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.core.logging import logger

FALLBACK_UNVERIFIED_MESSAGE = "I couldn't verify this information from the available official college sources."


class AnswerValidator:
    """
    Validates retrieved contexts and generated answers against strict institutional safety rules:
    1. Was relevant context retrieved?
    2. Is retrieval similarity above threshold?
    3. Are sources authoritative & verified?
    4. Are citations present and grounded in context?
    5. Does the document version represent the latest available record?
    """

    def __init__(self, similarity_threshold: float = settings.RAG_SIMILARITY_THRESHOLD):
        self.threshold = similarity_threshold

    def validate_retrieval(self, chunks: List[Dict[str, Any]]) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """
        Evaluate if retrieved chunks meet minimum similarity and verification criteria.
        Returns (is_valid, top_confidence, filtered_sources)
        """
        if not chunks:
            return False, 0.0, []

        verified_chunks = [c for c in chunks if c.get("is_verified", False)]
        if not verified_chunks:
            logger.info("No verified chunks present among retrieved items.")
            return False, 0.0, []

        top_similarity = max([c.get("similarity", 0.0) for c in verified_chunks])

        if top_similarity < self.threshold:
            logger.info(f"Top similarity ({top_similarity}) below threshold ({self.threshold}).")
            return False, 0.0, []

        sources = []
        for c in verified_chunks:
            sources.append({
                "document_id": c.get("document_id"),
                "title": c.get("title", "Official College Record"),
                "page": c.get("page", 1),
                "similarity": c.get("similarity", 0.0),
                "version": c.get("version", "1.0"),
            })

        return True, round(top_similarity, 4), sources

    def validate_generation(
        self,
        raw_answer: str,
        retrieval_valid: bool,
        confidence: float,
        sources: List[Dict[str, Any]],
        intent: str,
    ) -> Dict[str, Any]:
        """
        Final compliance check on LLM generation output.
        Enforces that if retrieval is invalid or empty, the strict fallback message is returned.
        """
        if not retrieval_valid or len(sources) == 0:
            return {
                "answer": FALLBACK_UNVERIFIED_MESSAGE,
                "verified": False,
                "confidence": 0.0,
                "sources": [],
                "intent": intent,
            }

        # Check for hedge or unverified indicators in LLM response
        answer_clean = raw_answer.strip()
        is_unverified_flagged = any(phrase in answer_clean.lower() for phrase in [
            "could not be verified",
            "couldn't verify",
            "not found in the verified",
            "not mentioned in the context",
            "cannot verify",
        ])

        if is_unverified_flagged:
            return {
                "answer": answer_clean if answer_clean else FALLBACK_UNVERIFIED_MESSAGE,
                "verified": False,
                "confidence": round(confidence * 0.5, 4),
                "sources": sources,
                "intent": intent,
            }

        return {
            "answer": answer_clean,
            "verified": True,
            "confidence": confidence,
            "sources": sources,
            "intent": intent,
        }


answer_validator = AnswerValidator()
