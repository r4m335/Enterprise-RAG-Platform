import os
import shutil
import uuid
from typing import BinaryIO
from core.config import settings
from .base import StorageProvider

class LocalStorage(StorageProvider):
    def __init__(self):
        self.base_path = settings.STORAGE_PATH
        os.makedirs(self.base_path, exist_ok=True)

    async def save(self, file: BinaryIO, path: str) -> str:
        # Securely join the path to prevent directory traversal
        full_path = os.path.abspath(os.path.join(self.base_path, path))
        if not full_path.startswith(os.path.abspath(self.base_path)):
            raise ValueError("Invalid storage path")
            
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "wb") as f:
            shutil.copyfileobj(file, f)
            
        return path

    async def get(self, path: str) -> BinaryIO:
        full_path = os.path.abspath(os.path.join(self.base_path, path))
        if not full_path.startswith(os.path.abspath(self.base_path)):
            raise ValueError("Invalid storage path")
            
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        return open(full_path, "rb")

    async def delete(self, path: str) -> bool:
        full_path = os.path.abspath(os.path.join(self.base_path, path))
        if not full_path.startswith(os.path.abspath(self.base_path)):
            raise ValueError("Invalid storage path")
            
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
