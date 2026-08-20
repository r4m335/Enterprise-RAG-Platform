from typing import Protocol, List

class EmbeddingProvider(Protocol):
    async def embed_documents(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        ...

    async def embed_query(
        self,
        text: str,
    ) -> List[float]:
        ...

    @property
    def dimension(self) -> int:
        ...

def get_embedding_provider() -> EmbeddingProvider:
    from core.config import settings
    if settings.EMBEDDING_PROVIDER.lower() == "local":
        from .local import LocalEmbeddingProvider
        return LocalEmbeddingProvider(model_name=settings.EMBEDDING_MODEL, dimension=settings.EMBEDDING_DIMENSION)
    elif settings.EMBEDDING_PROVIDER.lower() == "openai":
        from .openai import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider(model_name=settings.EMBEDDING_MODEL, dimension=settings.EMBEDDING_DIMENSION)
    else:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
