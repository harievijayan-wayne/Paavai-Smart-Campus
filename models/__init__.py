from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.department import Department
from app.models.user import User, StudentProfile, FacultyProfile
from app.models.grievance import Grievance, GrievanceHistory, StudentRequest
from app.models.announcement import Announcement, Event
from app.models.opportunity import Opportunity
from app.models.document import Document, DocumentChunk
from app.models.chat import Conversation, Message, AIInteraction
from app.models.notification import Notification

__all__ = [
    "Base",
    "TimestampMixin",
    "Department",
    "User",
    "StudentProfile",
    "FacultyProfile",
    "Grievance",
    "GrievanceHistory",
    "StudentRequest",
    "Announcement",
    "Event",
    "Opportunity",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "AIInteraction",
    "Notification",
]
