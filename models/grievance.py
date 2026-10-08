from typing import List, Optional, Any, Dict
from datetime import datetime
from sqlalchemy import String, Text, Float, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Grievance(Base, TimestampMixin):
    """Smart grievance ticket raised by students and processed through automated triage."""
    __tablename__ = "grievances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    ticket_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # e.g. "Laboratory", "Hostel", "Transport"
    priority: Mapped[str] = mapped_column(String(20), index=True, default="medium", nullable=False) # "low", "medium", "high", "critical"
    status: Mapped[str] = mapped_column(String(20), index=True, default="submitted", nullable=False) # "submitted", "assigned", "in_progress", "resolved", "closed"

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assigned_faculty_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True)

    attachments: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], back_populates="grievances_raised")
    assigned_faculty: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_faculty_id], back_populates="grievances_assigned")
    history: Mapped[List["GrievanceHistory"]] = relationship("GrievanceHistory", back_populates="grievance", cascade="all, delete-orphan", order_by="GrievanceHistory.created_at")


class GrievanceHistory(Base, TimestampMixin):
    """Audit log tracking state transitions and faculty actions on grievances."""
    __tablename__ = "grievance_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    grievance_id: Mapped[str] = mapped_column(String(36), ForeignKey("grievances.id", ondelete="CASCADE"), index=True, nullable=False)
    from_status: Mapped[str] = mapped_column(String(20), nullable=False)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    action_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    grievance: Mapped["Grievance"] = relationship("Grievance", back_populates="history")
    actor: Mapped["User"] = relationship("User")


class StudentRequest(Base, TimestampMixin):
    """Institutional requests such as Bonafide certificates, OD permissions, and Gate outpasses."""
    __tablename__ = "student_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # "bonafide", "od", "gate_pass", "medical_leave"
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, default="pending", nullable=False) # "pending", "approved", "rejected"
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], back_populates="student_requests")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id])
