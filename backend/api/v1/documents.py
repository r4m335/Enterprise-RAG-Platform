import uuid
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_db, get_current_user
from models.user import User
from schemas.document import UploadResponse, DocumentResponse
from services.document_service import process_upload

router = APIRouter()

@router.post("/", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document for processing.
    Supported types: PDF, DOCX, TXT, MD.
    Max size: 50MB.
    """
    return await process_upload(file, current_user.id, db)
