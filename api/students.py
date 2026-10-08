from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserResponse, StudentProfileResponse, StudentProfileUpdate

router = APIRouter(prefix="/api/students", tags=["Student Portal"])


@router.get("/profile", response_model=UserResponse)
async def get_student_profile(
    current_user: User = Depends(require_role(["student"])),
):
    """Retrieve full profile details for the authenticated student."""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_student_profile(
    data: StudentProfileUpdate,
    current_user: User = Depends(require_role(["student"])),
    db: AsyncSession = Depends(get_db),
):
    """Update editable student profile properties."""
    user_repo = UserRepository(db)
    if not current_user.student_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    profile = current_user.student_profile
    if data.semester is not None:
        profile.semester = data.semester
    if data.section is not None:
        profile.section = data.section
    if data.cgpa is not None:
        profile.cgpa = data.cgpa
    if data.attendance_percentage is not None:
        profile.attendance_percentage = data.attendance_percentage

    await db.flush()
    return await user_repo.get_with_profile(current_user.id)


@router.get("/academic-summary")
async def get_academic_summary(
    current_user: User = Depends(require_role(["student"])),
):
    """Get high-level academic metric summary (CGPA, attendance, semester, arrears)."""
    p = current_user.student_profile
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile missing")

    return {
        "reg_number": p.reg_number,
        "department": p.department.name if p.department else "General Engineering",
        "semester": p.semester,
        "section": p.section,
        "cgpa": p.cgpa,
        "attendance_percentage": p.attendance_percentage,
        "standing_arrears": p.standing_arrears,
        "status": "Good Standing" if p.standing_arrears == 0 else f"{p.standing_arrears} Pending Arrears",
    }
