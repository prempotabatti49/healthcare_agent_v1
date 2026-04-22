"""Document upload and management endpoints."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.queries import create_document, get_document, get_user_documents
from app.db.session import get_db
from app.models.db_models import DocumentType, User
from app.models.pydantic_models import DocumentOut, DocumentUploadResponse
from app.services import s3_service
from app.services.document_processor import (
    SUPPORTED_EXTENSIONS,
    pages_to_text,
    process_document,
)
from app.services.supermemory import supermemory_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.other),
    notes: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a medical document (PDF, image, PPT).

    Pipeline:
      1. Validate file type
      2. Upload raw file to S3 for archival (uncomment when S3 is configured)
      3. Extract text from the document (PDF text or GPT-4o Vision for images)
      4. Store extracted text in SuperMemory vector DB
      5. Save a record to PostgreSQL
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    filename = file.filename or f"upload_{current_user.id}{ext}"

    # ── Step 1: Upload original file to S3 ───────────────────────────────────
    # Uncomment when S3 is configured in your environment:
    # s3_key = s3_service.upload_document(file_bytes, filename, current_user.id, document_type.value)
    s3_key = None

    # ── Step 2: Extract text from the document ────────────────────────────────
    # Uncomment when document processing dependencies are installed:
    # try:
    #     pages = process_document(file_bytes, filename)
    #     full_text = pages_to_text(pages)
    # except Exception as exc:
    #     raise HTTPException(status_code=422, detail=f"Document processing failed: {exc}")
    pages = []
    full_text = ""

    # ── Step 3: Store extracted text in SuperMemory ───────────────────────────
    metadata = {
        "filename": filename,
        "document_type": document_type.value,
        "user_id": current_user.id,
        "notes": notes,
    }
    supermemory_doc_id = supermemory_service.add_document(
        user_id=current_user.id,
        content=full_text,
        metadata=metadata,
    )

    # ── Step 4: Save record to PostgreSQL ─────────────────────────────────────
    doc = create_document(
        db,
        user_id=current_user.id,
        filename=filename,
        document_type=document_type,
        s3_key=s3_key,
        supermemory_doc_id=supermemory_doc_id,
        notes=notes or None,
    )

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=filename,
        document_type=document_type,
        s3_key=s3_key,
        message=f"Document stored. Extracted {len(pages)} page(s).",
    )


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all documents uploaded by the logged-in user."""
    return get_user_documents(db, current_user.id)


@router.get("/{document_id}/download-url")
def get_download_url(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a temporary pre-signed URL to download the original document from S3."""
    doc = get_document(db, document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc.s3_key:
        raise HTTPException(status_code=404, detail="No file stored for this document.")

    url = s3_service.get_presigned_url(doc.s3_key)
    if not url:
        raise HTTPException(status_code=503, detail="Could not generate download URL.")
    return {"url": url, "expires_in_seconds": 3600}
