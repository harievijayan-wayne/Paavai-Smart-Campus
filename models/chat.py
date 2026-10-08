from typing import List, Optional, Any, Dict
from sqlalchemy import String, Text, Boolean, Float, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Conversation(Base, TimestampMixin):
    """User conversation thread with the Campus AI Assistant."""
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="New Academic Inquiry", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base, TimestampMixin):
    """Chat message bubble exchanged between student and AI assistant."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False) # "user", "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class AIInteraction(Base, TimestampMixin):
    """Performance telemetry and audit record for every AI query."""
    __tablename__ = "ai_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    intent_detected: Mapped[str] = mapped_column(String(50), nullable=False)
    intent_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    chunks_retrieved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ollama_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verified_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
