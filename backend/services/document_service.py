import os
import filetype
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.document import Document, DocumentStatus
from schemas.document import UploadResponse
from services.storage import get_storage_provider
import uuid

from repositories.document import DocumentRepository

# 50 MB limit
MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".docx"
}

def validate_file(file: UploadFile, file_bytes: bytes):
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file extension: {ext}")
        
    kind = filetype.guess(file_bytes)
    detected_mime = kind.mime if kind else None
    
    if detected_mime is None:
        # If filetype can't guess, check if it's valid UTF-8 text (for txt/md)
        try:
            file_bytes.decode('utf-8')
            detected_mime = "text/plain" if ext == ".txt" else "text/markdown"
        except UnicodeDecodeError:
            raise HTTPException(status_code=415, detail="Unable to determine file type or invalid text encoding.")
            
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {detected_mime}")
        
    return detected_mime, ext

async def process_upload(file: UploadFile, user_id: uuid.UUID, db: AsyncSession) -> UploadResponse:
    # Read the file for validation
    file_bytes = await file.read()
    
    detected_mime, ext = validate_file(file, file_bytes)
    
    # Reset file pointer for storage saving
    await file.seek(0)
    
    # Pre-generate document ID
    document_id = uuid.uuid4()
    
    # Structured storage path
    storage_path_relative = f"{user_id}/{document_id}/original{ext}"
    
    # Save to storage
    storage = get_storage_provider()
    # file.file is a SpooledTemporaryFile which acts like a BinaryIO
    storage_path = await storage.save(file.file, storage_path_relative)
    
    # Create Document row using repository
    repo = DocumentRepository(db)
    doc = await repo.create_document(
        user_id=user_id,
        document_id=document_id,
        filename=file.filename,
        mime_type=detected_mime,
        file_size=len(file_bytes),
        storage_path=storage_path,
        storage_provider="LOCAL"
    )
    
    # Enqueue Celery Task
    from workers.tasks.document_processing import process_document_task
    process_document_task.delay(str(doc.id))
    
    return UploadResponse(
        message="File uploaded successfully and processing started.",
        document_id=doc.id
    )
