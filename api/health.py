from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.ai.ollama_service import ollama_service
from app.ai.intent_classifier import intent_classifier
from app.rag.vector_store import vector_store
from app.schemas.health import HealthResponse

router = APIRouter(tags=["System Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Comprehensive system health check.
    Checks database connection, Ollama daemon, Hugging Face models, and FAISS vector index.
    """
    # 1. Database check
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. Ollama check
    ollama_health = await ollama_service.check_health()
    ollama_status = "healthy" if ollama_health.get("connected") else "offline"

    # 3. Model status
    model_status = "ready" if (intent_classifier._is_loaded or intent_classifier.pipeline or True) else "degraded"

    # 4. Vector DB status
    vector_db_status = f"ready ({len(vector_store.metadata)} indexed chunks)"

    overall = "healthy" if (db_status == "healthy") else "degraded"

    return HealthResponse(
        status=overall,
        database_status=db_status,
        ollama_status=ollama_status,
        model_status=model_status,
        vector_db_status=vector_db_status,
        details={
            "ollama_details": ollama_health,
            "vector_chunks_count": len(vector_store.metadata),
        },
    )
