from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message, AIInteraction
from app.repositories.chat_repo import ChatRepository
from app.rag.rag_engine import rag_engine
from app.ai.intent_classifier import intent_classifier
from app.schemas.ai import (
    AskRequest,
    AskResponse,
    IntentClassificationResult,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter(prefix="/api/ai", tags=["AI Academic Assistant"])


@router.post("/ask", response_model=AskResponse)
async def ask_assistant(
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RAG-grounded College Academic Assistant endpoint.
    Performs intent detection, verified document retrieval, threshold validation,
    Ollama LLM generation adhering to 10 strict institutional rules, and source citation.
    """
    chat_repo = ChatRepository(db)

    # Resolve or create conversation thread
    conversation = None
    conversation_history = []
    if request.conversation_id:
        conversation = await chat_repo.get_with_messages(request.conversation_id, current_user.id)
        if conversation:
            for m in conversation.messages[-6:]:
                conversation_history.append({"role": m.sender_role, "content": m.content})
    else:
        # Create new conversation
        short_title = request.question[:40] + ("..." if len(request.question) > 40 else "")
        conversation = Conversation(
            user_id=current_user.id,
            title=short_title,
        )
        await chat_repo.create(conversation)

    # Record user message
    user_msg = Message(
        conversation_id=conversation.id,
        sender_role="user",
        content=request.question,
    )
    await chat_repo.add_message(user_msg)

    # Execute RAG Pipeline
    rag_result = await rag_engine.answer_question(
        question=request.question,
        conversation_history=conversation_history,
    )

    # Record assistant message
    sources_data = [s for s in rag_result.get("sources", [])]
    assistant_msg = Message(
        conversation_id=conversation.id,
        sender_role="assistant",
        content=rag_result["answer"],
        intent=rag_result.get("intent"),
        verified=rag_result.get("verified", False),
        confidence=rag_result.get("confidence", 0.0),
        sources=sources_data,
        latency_ms=rag_result.get("latency_ms"),
    )
    await chat_repo.add_message(assistant_msg)

    # Log telemetry for monitoring
    interaction = AIInteraction(
        user_id=current_user.id,
        query=request.question,
        intent_detected=rag_result.get("intent", "general"),
        intent_confidence=rag_result.get("confidence", 0.0),
        chunks_retrieved=len(sources_data),
        similarity_score=rag_result.get("confidence", 0.0),
        ollama_latency_ms=rag_result.get("ollama_latency_ms", 0.0),
        total_latency_ms=rag_result.get("latency_ms", 0.0),
        verified_status=rag_result.get("verified", False),
    )
    await chat_repo.log_interaction(interaction)

    return AskResponse(
        answer=rag_result["answer"],
        verified=rag_result["verified"],
        confidence=rag_result["confidence"],
        intent=rag_result["intent"],
        sources=rag_result["sources"],
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        latency_ms=rag_result.get("latency_ms"),
    )


@router.post("/classify-intent", response_model=IntentClassificationResult)
async def classify_intent_endpoint(
    request: AskRequest,
    current_user: User = Depends(get_current_user),
):
    """Direct intent classification pipeline using Hugging Face Transformer."""
    result = intent_classifier.predict(request.question)
    return IntentClassificationResult(
        intent=result["intent"],
        confidence=result["confidence"],
        probabilities=result.get("probabilities"),
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_user_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve history of AI inquiry threads for the logged-in student or faculty."""
    chat_repo = ChatRepository(db)
    return await chat_repo.list_conversations(user_id=current_user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_thread(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full dialogue thread with timestamps, citations, and confidence scores."""
    chat_repo = ChatRepository(db)
    conversation = await chat_repo.get_with_messages(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation
