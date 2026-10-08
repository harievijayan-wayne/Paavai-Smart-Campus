from app.api.auth import router as auth_router
from app.api.ai import router as ai_router
from app.api.grievances import router as grievances_router
from app.api.documents import router as documents_router
from app.api.announcements import router as announcements_router
from app.api.opportunities import router as opportunities_router
from app.api.students import router as students_router
from app.api.faculty import router as faculty_router
from app.api.admin import router as admin_router
from app.api.notifications import router as notifications_router
from app.api.health import router as health_router

__all__ = [
    "auth_router",
    "ai_router",
    "grievances_router",
    "documents_router",
    "announcements_router",
    "opportunities_router",
    "students_router",
    "faculty_router",
    "admin_router",
    "notifications_router",
    "health_router",
]
