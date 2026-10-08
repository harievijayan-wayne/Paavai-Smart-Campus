from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.services.announcement_service import AnnouncementService
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    EventCreate,
    EventResponse,
)

router = APIRouter(prefix="/api/announcements", tags=["Announcements & Events"])


@router.get("", response_model=List[AnnouncementResponse])
async def list_announcements(
    search: Optional[str] = None,
    category: Optional[str] = None,
    department_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List announcements with search, category filtering, and role segregation.
    Students only see published notices targeted to them or 'all'.
    """
    service = AnnouncementService(db)
    is_published = True if current_user.role == "student" else None
    return await service.repo.list_announcements(
        query=search,
        category=category,
        target_role=current_user.role,
        is_published=is_published,
        department_id=department_id,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: AnnouncementCreate,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Create a new campus announcement."""
    service = AnnouncementService(db)
    ann = await service.create_announcement(author_id=current_user.id, data=data)
    return await service.repo.get_with_author(ann.id)


@router.get("/events", response_model=List[EventResponse])
async def list_events(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List scheduled campus events, workshops, symposiums, and hackathons."""
    service = AnnouncementService(db)
    return await service.repo.list_events(skip=skip, limit=limit)


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Create and publish a new campus event."""
    service = AnnouncementService(db)
    event = await service.create_event(organizer_id=current_user.id, data=data)
    return event


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve announcement details and increment view count."""
    service = AnnouncementService(db)
    ann = await service.repo.get_with_author(announcement_id)
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    await service.repo.increment_views(announcement_id)
    return ann


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: str,
    data: AnnouncementUpdate,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Update existing announcement."""
    service = AnnouncementService(db)
    ann = await service.update_announcement(announcement_id, data)
    return await service.repo.get_with_author(ann.id)


@router.patch("/{announcement_id}/publish", response_model=AnnouncementResponse)
async def toggle_announcement_publish(
    announcement_id: str,
    is_published: bool = True,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Publish or unpublish an announcement."""
    service = AnnouncementService(db)
    ann = await service.toggle_publish(announcement_id, is_published)
    return await service.repo.get_with_author(ann.id)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """Delete an announcement."""
    service = AnnouncementService(db)
    await service.delete_announcement(announcement_id)
    return None
