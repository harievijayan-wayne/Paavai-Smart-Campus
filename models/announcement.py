from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Announcement(Base, TimestampMixin):
    """Broadcast notices, circulars, and institutional alerts."""
    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="General", index=True, nullable=False)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    department_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    attachment_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    target_audience: Mapped[str] = mapped_column(String(20), default="all", nullable=False) # "all", "students", "faculty"

    # Relationships
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="announcements")
    author: Mapped["User"] = relationship("User")


class Event(Base, TimestampMixin):
    """Campus calendar events, technical symposiums, hackathons, and guest lectures."""
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    venue: Mapped[str] = mapped_column(String(150), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="Academic", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    coordinator_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    coordinator: Mapped[Optional["User"]] = relationship("User")
