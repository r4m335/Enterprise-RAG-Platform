from pydantic import BaseModel, UUID4, ConfigDict
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    filename: str
    original_filename: str
    mime_type: Optional[str]
    file_size: Optional[int]
    processing_status: str
    processing_error: Optional[str]
    embedding_status: str
    embedding_error: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UploadResponse(BaseModel):
    message: str
    document_id: UUID4
