from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.repositories.grievance_repo import GrievanceRepository
from app.schemas.user import UserResponse
from app.schemas.grievance import GrievanceResponse

router = APIRouter(prefix="/api/faculty", tags=["Faculty Portal"])


@router.get("/profile", response_model=UserResponse)
async def get_faculty_profile(
    current_user: User = Depends(require_role(["faculty"])),
):
    """Retrieve profile and assigned departmental leadership for authenticated faculty."""
    return current_user


@router.get("/assigned-grievances", response_model=List[GrievanceResponse])
async def get_assigned_grievances(
    current_user: User = Depends(require_role(["faculty"])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve grievances specifically assigned to this faculty member."""
    grievance_repo = GrievanceRepository(db)
    return await grievance_repo.list_grievances(faculty_id=current_user.id)


@router.get("/department-students", response_model=List[UserResponse])
async def get_department_students(
    current_user: User = Depends(require_role(["faculty"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve student records belonging ONLY to the faculty's assigned department.
    Strictly prohibits viewing students from other departments.
    """
    if not current_user.faculty_profile or not current_user.faculty_profile.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faculty member is not assigned to any departmental division",
        )

    user_repo = UserRepository(db)
    dept_id = current_user.faculty_profile.department_id
    students = await user_repo.get_students_by_department(dept_id)
    return students
