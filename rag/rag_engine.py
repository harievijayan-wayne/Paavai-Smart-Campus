import time
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.ai.intent_classifier import intent_classifier
from app.ai.ollama_service import ollama_service
from app.rag.embedding_service import embedding_service
from app.rag.vector_store import vector_store
from app.rag.answer_validator import answer_validator, FALLBACK_UNVERIFIED_MESSAGE


class RAGEngine:
    """
    Complete production RAG pipeline for Paavai Smart Campus AI.
    Integrates intent classification, vector similarity search, minimum threshold gating,
    Ollama LLM generation with strict institutional rules, and source citation validation.
    """

    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD

    async def answer_question(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline for student or faculty inquiries.
        """
        start_time = time.time()

        # Step 1: Detect intent
        intent_res = intent_classifier.predict(question)
        detected_intent = intent_res.get("intent", "general")

        # Step 2: Embed query
        query_vector = embedding_service.embed_query(question)

        # Step 3 & 4: Retrieve top relevant verified chunks from vector store
        retrieved_chunks = vector_store.similarity_search(
            query_vector=query_vector,
            top_k=self.top_k,
            verified_only=True,
            min_threshold=self.similarity_threshold,
        )

        # Step 5 & 6: Validate retrieval similarity against threshold
        retrieval_valid, confidence, sources = answer_validator.validate_retrieval(retrieved_chunks)

        # Guard: If no sufficiently relevant verified source exists, DO NOT ask Ollama to guess
        if not retrieval_valid or len(sources) == 0:
            logger.info(f"Query '{question}' yielded no verified source meeting threshold. Returning fallback.")
            total_latency = (time.time() - start_time) * 1000
            return {
                "answer": FALLBACK_UNVERIFIED_MESSAGE,
                "verified": False,
                "confidence": 0.0,
                "sources": [],
                "intent": detected_intent,
                "latency_ms": round(total_latency, 2),
            }

        # Step 7 & 8: Send only verified relevant context to Ollama
        gen_result = await ollama_service.generate_rag_response(
            question=question,
            context_chunks=retrieved_chunks,
            conversation_history=conversation_history,
        )

        raw_answer = gen_result.get("answer", "")
        ollama_latency = gen_result.get("latency_ms", 0.0)

        # Step 9 & 10: Answer validation & citation attachment
        final_validation = answer_validator.validate_generation(
            raw_answer=raw_answer,
            retrieval_valid=retrieval_valid,
            confidence=confidence,
            sources=sources,
            intent=detected_intent,
        )

        total_latency = (time.time() - start_time) * 1000
        final_validation["latency_ms"] = round(total_latency, 2)
        final_validation["ollama_latency_ms"] = round(ollama_latency, 2)

        return final_validation


rag_engine = RAGEngine()
