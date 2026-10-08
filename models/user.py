from typing import List, Optional
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """Core user entity representing Students, Faculty, and Administrators."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # "student", "faculty", "admin"
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # One-to-one profiles
    student_profile: Mapped[Optional["StudentProfile"]] = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile: Mapped[Optional["FacultyProfile"]] = relationship("FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Activity relationships
    grievances_raised: Mapped[List["Grievance"]] = relationship("Grievance", foreign_keys="Grievance.student_id", back_populates="student")
    grievances_assigned: Mapped[List["Grievance"]] = relationship("Grievance", foreign_keys="Grievance.assigned_faculty_id", back_populates="assigned_faculty")
    student_requests: Mapped[List["StudentRequest"]] = relationship("StudentRequest", foreign_keys="StudentRequest.student_id", back_populates="student")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")


class StudentProfile(Base, TimestampMixin):
    """Academic record details specific to undergraduate/postgraduate students."""
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    reg_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), index=True, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    section: Mapped[str] = mapped_column(String(5), default="A", nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    standing_arrears: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attendance_percentage: Mapped[float] = mapped_column(Float, default=85.0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    department: Mapped["Department"] = relationship("Department", back_populates="students")


class FacultyProfile(Base, TimestampMixin):
    """Institutional faculty and departmental leadership details."""
    __tablename__ = "faculty_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), index=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(100), default="Assistant Professor", nullable=False)
    cabin_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="faculty_profile")
    department: Mapped["Department"] = relationship("Department", back_populates="faculty_members")
