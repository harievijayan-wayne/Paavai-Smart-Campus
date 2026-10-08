from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.services.grievance_service import GrievanceService
from app.schemas.grievance import (
    GrievanceCreate,
    GrievanceClassificationRequest,
    GrievanceClassificationResult,
    GrievanceUpdateStatus,
    GrievanceResponse,
    StudentRequestCreate,
    StudentRequestUpdateStatus,
    StudentRequestResponse,
)

router = APIRouter(prefix="/api/grievances", tags=["Grievances & Requests"])


@router.post("/classify", response_model=GrievanceClassificationResult)
async def classify_grievance_preview(
    request: GrievanceClassificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Automated AI classification preview.
    Predicts category, priority, department, and confidence before submission.
    """
    service = GrievanceService(db)
    return service.classify_grievance(request)


@router.post("", response_model=GrievanceResponse, status_code=status.HTTP_201_CREATED)
async def create_grievance(
    data: GrievanceCreate,
    current_user: User = Depends(require_role(["student", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new student grievance.
    Automatically classifies category, priority, and department, while allowing
    the student to confirm or edit before final ticket generation.
    """
    service = GrievanceService(db)
    grievance = await service.create_grievance(student_id=current_user.id, data=data)
    # Reload with full relations
    full_grievance = await service.repo.get_with_details(grievance.id)
    return full_grievance


@router.get("", response_model=List[GrievanceResponse])
async def list_grievances(
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List grievances based on role:
    - Students see only their own tickets.
    - Faculty see tickets belonging to their assigned department.
    - Admins see all tickets.
    """
    service = GrievanceService(db)
    return await service.list_grievances(
        user_id=current_user.id,
        role=current_user.role,
        status=status_filter,
        category=category_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/{grievance_id}", response_model=GrievanceResponse)
async def get_grievance_details(
    grievance_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete grievance record including full state transition audit history."""
    service = GrievanceService(db)
    grievance = await service.repo.get_with_details(grievance_id)
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")

    # Access check: students can only view their own
    if current_user.role == "student" and grievance.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this ticket")

    return grievance


@router.patch("/{grievance_id}/status", response_model=GrievanceResponse)
async def update_grievance_status(
    grievance_id: str,
    update_data: GrievanceUpdateStatus,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Transition grievance status (submitted -> assigned -> in_progress -> resolved -> closed).
    Maintains an immutable audit trail with actor details and notes.
    """
    service = GrievanceService(db)
    updated = await service.update_status(
        grievance_id=grievance_id,
        user_id=current_user.id,
        user_role=current_user.role,
        update_data=update_data,
    )
    return await service.repo.get_with_details(updated.id)


# Student Administrative Requests (Bonafide, OD, Gate Pass, etc.)
@router.post("/requests", response_model=StudentRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_student_request(
    data: StudentRequestCreate,
    current_user: User = Depends(require_role(["student", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Submit formal requests for Bonafide certificate, OD permission, or Gate outpass."""
    service = GrievanceService(db)
    req = await service.create_student_request(student_id=current_user.id, data=data)
    return await service.repo.get_request_by_id(req.id)


@router.get("/requests", response_model=List[StudentRequestResponse])
async def list_student_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List administrative requests for the current user or department."""
    service = GrievanceService(db)
    student_id = current_user.id if current_user.role == "student" else None
    return await service.repo.list_requests(student_id=student_id, status=status_filter)


@router.patch("/requests/{request_id}/status", response_model=StudentRequestResponse)
async def update_student_request_status(
    request_id: str,
    data: StudentRequestUpdateStatus,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a student administrative request."""
    service = GrievanceService(db)
    updated = await service.update_request_status(req_id=request_id, approver_id=current_user.id, data=data)
    return await service.repo.get_request_by_id(updated.id)
