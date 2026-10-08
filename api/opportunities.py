from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.services.opportunity_service import OpportunityService
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityResponse,
    OpportunityRecommendation,
)

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities & Placements"])


@router.get("", response_model=List[OpportunityResponse])
async def list_opportunities(
    search: Optional[str] = None,
    opp_type: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List career opportunities, internships, hackathons, and scholarships."""
    service = OpportunityService(db)
    return await service.repo.list_opportunities(
        query=search,
        opp_type=opp_type,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.get("/recommended", response_model=List[OpportunityRecommendation])
async def get_recommended_opportunities(
    current_user: User = Depends(require_role(["student"])),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-driven recommendation engine matching student's CGPA, semester,
    and department against available opportunities.
    """
    service = OpportunityService(db)
    return await service.get_recommended_for_student(student_user_id=current_user.id)


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: OpportunityCreate,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Create and post a new opportunity listing."""
    service = OpportunityService(db)
    return await service.create_opportunity(data)


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single opportunity listing."""
    service = OpportunityService(db)
    opp = await service.repo.get_by_id(opportunity_id)
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opp


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    data: OpportunityUpdate,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Update opportunity."""
    service = OpportunityService(db)
    return await service.update_opportunity(opportunity_id, data)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(
    opportunity_id: str,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Delete opportunity."""
    service = OpportunityService(db)
    await service.delete_opportunity(opportunity_id)
    return None
