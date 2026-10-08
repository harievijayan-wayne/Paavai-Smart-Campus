import time
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from app.core.config import settings
from app.core.logging import logger

SYSTEM_PROMPT = """You are Paavai Smart Campus AI.

Your job is to answer questions using only the verified context supplied by the application.

Rules:
1. Never invent college-specific information.
2. Never guess dates, fees, regulations, policies, procedures or faculty information.
3. Never override official source information.
4. If the retrieved context does not answer the question, say that the information could not be verified.
5. Clearly distinguish verified information from general guidance.
6. Cite the source documents supplied in the context.
7. Do not fabricate citations.
8. Do not claim certainty when evidence is insufficient.
9. Prefer the latest verified document when multiple versions exist.
10. If two official sources conflict, report the conflict instead of choosing arbitrarily."""


class OllamaService:
    """
    Ollama integration service using asynchronous HTTP client for local LLM inference.
    Supports chat completion, streaming, structured JSON output, timeout handling,
    and connection health checks.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> Dict[str, Any]:
        """Verify connectivity to local Ollama instance and check model availability."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = any(self.model in m for m in models)
                    return {
                        "status": "healthy",
                        "connected": True,
                        "available_models": models,
                        "configured_model": self.model,
                        "model_ready": model_found,
                    }
                return {
                    "status": "unhealthy",
                    "connected": True,
                    "error": f"Unexpected status code: {res.status_code}",
                }
        except Exception as e:
            logger.warning(f"Ollama health check connection failed: {str(e)}")
            return {
                "status": "offline",
                "connected": False,
                "error": str(e),
                "configured_model": self.model,
            }

    async def generate_rag_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate answer strictly adhering to the 10 system prompt rules.
        Injects verified college context chunks and citations.
        """
        start_time = time.time()

        # Build context prompt
        formatted_context = ""
        for i, chunk in enumerate(context_chunks, 1):
            doc_title = chunk.get("title", "Official College Document")
            page = chunk.get("page", 1)
            content = chunk.get("content", "").strip()
            version = chunk.get("version", "1.0")
            formatted_context += (
                f"\n[Source {i} | Document: {doc_title} | Version: {version} | Page: {page}]\n"
                f"{content}\n"
            )

        user_content = (
            f"Here is the verified college context:\n"
            f"----------------------------------------\n"
            f"{formatted_context}\n"
            f"----------------------------------------\n\n"
            f"Student Question: {question}\n\n"
            f"Instructions:\n"
            f"- Answer the question based solely on the verified context above.\n"
            f"- Explicitly cite source names and page numbers.\n"
            f"- If the context is insufficient, state that the information could not be verified."
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if conversation_history:
            # Include recent chat history (last 4 messages) for continuity
            for msg in conversation_history[-4:]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        messages.append({"role": "user", "content": user_content})

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temperature for strict factual accuracy
                        "top_p": 0.9,
                    },
                }
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                answer = data.get("message", {}).get("content", "").strip()
                latency_ms = (time.time() - start_time) * 1000

                return {
                    "answer": answer,
                    "latency_ms": latency_ms,
                    "model_used": self.model,
                    "success": True,
                }
        except httpx.ConnectError:
            logger.error("Ollama service is offline or unreachable at base URL.")
            return {
                "answer": "Unable to connect to the local campus AI engine. Please ensure Ollama is running.",
                "latency_ms": (time.time() - start_time) * 1000,
                "model_used": self.model,
                "success": False,
                "error": "connection_error",
            }
        except httpx.TimeoutException:
            logger.error("Ollama inference request timed out.")
            return {
                "answer": "The AI assistant request timed out. Please try again with a more specific query.",
                "latency_ms": (time.time() - start_time) * 1000,
                "model_used": self.model,
                "success": False,
                "error": "timeout",
            }
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            return {
                "answer": "An error occurred while generating the campus response.",
                "latency_ms": (time.time() - start_time) * 1000,
                "model_used": self.model,
                "success": False,
                "error": str(e),
            }

    async def stream_rag_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """Streaming generator for real-time token streaming to frontend."""
        formatted_context = "\n".join(
            [f"[Source {i+1} | {c.get('title')} (p.{c.get('page')})]: {c.get('content')}" for i, c in enumerate(context_chunks)]
        )
        user_content = f"Verified College Context:\n{formatted_context}\n\nQuestion: {question}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": True, "options": {"temperature": 0.2}},
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            chunk_data = json.loads(line)
                            token = chunk_data.get("message", {}).get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue


ollama_service = OllamaService()
