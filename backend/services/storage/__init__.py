from .base import StorageProvider
from .local import LocalStorage

def get_storage_provider(provider_type: str = "LOCAL") -> StorageProvider:
    if provider_type == "LOCAL":
        return LocalStorage()
    # Support for S3 or others can be added here
    raise ValueError(f"Unsupported storage provider: {provider_type}")
