from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Department(Base, TimestampMixin):
    """Academic and administrative departments within Paavai College of Engineering."""
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False) # e.g. "CSE", "ECE"
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    building_block: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hod_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    students: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="department")
    faculty_members: Mapped[List["FacultyProfile"]] = relationship("FacultyProfile", back_populates="department")
    announcements: Mapped[List["Announcement"]] = relationship("Announcement", back_populates="department")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="department")
