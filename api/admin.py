from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.document import Document
from app.models.opportunity import Opportunity
from app.models.chat import AIInteraction
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserResponse, DepartmentResponse

router = APIRouter(prefix="/api/admin", tags=["Administrator Portal"])


@router.get("/stats")
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """System-wide operational metrics and telemetry for campus administrators."""
    # Count users by role
    users_q = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    role_counts = {r[0]: r[1] for r in users_q.all()}

    # Count grievances by status
    grv_q = await db.execute(select(Grievance.status, func.count(Grievance.id)).group_by(Grievance.status))
    grievance_status_counts = {r[0]: r[1] for r in grv_q.all()}

    # Count documents
    doc_total_q = await db.execute(select(func.count(Document.id)))
    doc_verified_q = await db.execute(select(func.count(Document.id)).where(Document.is_verified == True))
    total_docs = doc_total_q.scalar() or 0
    verified_docs = doc_verified_q.scalar() or 0

    # Count opportunities
    opp_q = await db.execute(select(func.count(Opportunity.id)).where(Opportunity.is_active == True))
    active_opps = opp_q.scalar() or 0

    # AI telemetry
    ai_q = await db.execute(select(func.count(AIInteraction.id)))
    total_interactions = ai_q.scalar() or 0

    return {
        "users": {
            "total": sum(role_counts.values()),
            "by_role": role_counts,
        },
        "grievances": {
            "total": sum(grievance_status_counts.values()),
            "by_status": grievance_status_counts,
        },
        "knowledge_base": {
            "total_documents": total_docs,
            "verified_documents": verified_docs,
            "pending_verification": total_docs - verified_docs,
        },
        "opportunities": {
            "active": active_opps,
        },
        "ai_engine": {
            "total_queries_served": total_interactions,
        },
    }


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """List all accounts across student, faculty, and administrative tiers."""
    user_repo = UserRepository(db)
    return await user_repo.list_all(skip=skip, limit=limit)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    new_role: str,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Change authorization role for a user."""
    if new_role not in ["student", "faculty", "admin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role specified")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = new_role
    await user_repo.update(user)
    return await user_repo.get_with_profile(user.id)


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(require_role(["admin", "faculty"])),
    db: AsyncSession = Depends(get_db),
):
    """List all official academic departments."""
    user_repo = UserRepository(db)
    return await user_repo.get_or_create_default_departments()


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    name: str,
    code: str,
    block: Optional[str] = None,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Add a new academic department to the institutional registry."""
    dept = Department(name=name, code=code.upper(), building_block=block)
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return dept
