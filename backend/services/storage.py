from abc import ABC, abstractmethod
import os
import shutil
from pathlib import Path
from loguru import logger
from core.config import settings

class StorageProvider(ABC):
    """Abstract interface for storage providers to ensure consistency across Local, S3, MinIO."""
    
    @abstractmethod
    async def save(self, file_name: str, content: bytes) -> str:
        """Saves a file and returns its path or URI."""
        pass

    @abstractmethod
    async def delete(self, file_name: str) -> bool:
        """Deletes a file and returns success status."""
        pass

    @abstractmethod
    async def download(self, file_name: str) -> bytes:
        """Downloads a file and returns its content as bytes."""
        pass

    @abstractmethod
    async def exists(self, file_name: str) -> bool:
        """Checks if a file exists."""
        pass


class LocalStorage(StorageProvider):
    """Local filesystem implementation of StorageProvider."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.uploads_path = self.base_path / "uploads"
        
        # Ensure directories exist
        self.uploads_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage initialized at {self.base_path}")

    def _get_path(self, file_name: str) -> Path:
        return self.uploads_path / file_name

    async def save(self, file_name: str, content: bytes) -> str:
        file_path = self._get_path(file_name)
        with open(file_path, "wb") as f:
            f.write(content)
        return str(file_path)

    async def delete(self, file_name: str) -> bool:
        file_path = self._get_path(file_name)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def download(self, file_name: str) -> bytes:
        file_path = self._get_path(file_name)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_name}")
        with open(file_path, "rb") as f:
            return f.read()

    async def exists(self, file_name: str) -> bool:
        return self._get_path(file_name).exists()
