from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageProvider(ABC):
    @abstractmethod
    async def save(self, file: BinaryIO, filename: str) -> str:
        """
        Saves a file to storage and returns the storage path/URI.
        """
        pass

    @abstractmethod
    async def get(self, path: str) -> BinaryIO:
        """
        Retrieves a file from storage.
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        Deletes a file from storage.
        """
        pass
