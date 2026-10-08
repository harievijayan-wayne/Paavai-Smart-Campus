from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentVerifyRequest

router = APIRouter(prefix="/api/documents", tags=["Knowledge Base & Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    department_id: Optional[str] = Form(None),
    version: str = Form("1.0"),
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload official institutional document (PDF, DOCX, TXT).
    Extracts text, splits into semantic chunks, generates embeddings,
    and indexes into FAISS vector store. Marked unverified until admin review.
    """
    service = DocumentService(db)
    doc = await service.upload_document(
        file=file,
        title=title,
        department_id=department_id,
        uploaded_by_user_id=current_user.id,
        version=version,
    )
    return await service.repo.get_with_chunks(doc.id)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    verified_only: Optional[bool] = None,
    department_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List uploaded knowledge base documents.
    Students see verified documents by default. Admins and faculty can filter by verification status.
    """
    service = DocumentService(db)
    # If student, default to verified only
    if current_user.role == "student" and verified_only is None:
        verified_only = True

    return await service.repo.list_documents(
        verified_only=verified_only,
        department_id=department_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve document details and its extracted chunk segments."""
    service = DocumentService(db)
    doc = await service.repo.get_with_chunks(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("/{document_id}/verify", response_model=DocumentResponse)
async def verify_document(
    document_id: str,
    payload: DocumentVerifyRequest = DocumentVerifyRequest(is_verified=True),
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify or unverify an institutional document.
    Only administrators have permission to verify documents for authoritative RAG retrieval.
    """
    service = DocumentService(db)
    updated = await service.verify_document(
        document_id=document_id,
        admin_user_id=current_user.id,
        is_verified=payload.is_verified,
    )
    return await service.repo.get_with_chunks(updated.id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete document and expunge its vector embeddings from FAISS.
    Restricted to campus administrators.
    """
    service = DocumentService(db)
    await service.delete_document(document_id)
    return None
