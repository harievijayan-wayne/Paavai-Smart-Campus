from typing import List, Optional
from datetime import date
from sqlalchemy import String, Text, Float, Integer, Boolean, Date, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Opportunity(Base, TimestampMixin):
    """Internships, placement drives, competitions, hackathons, and certifications."""
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), index=True, nullable=False) # "Internship", "Hackathon", "Job", "Certification", "Competition"
    organization: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_criteria: Mapped[str] = mapped_column(String(255), nullable=False)

    min_cgpa: Mapped[float] = mapped_column(Float, default=6.0, nullable=False)
    max_arrears: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_departments: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True) # e.g. ["CSE", "IT"]
    skills_required: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True) # e.g. ["Python", "React"]

    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    stipend_or_prize: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(100), default="Campus / Hybrid", nullable=False)
    apply_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
