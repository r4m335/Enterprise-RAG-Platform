from typing import List

class OpenAIEmbeddingProvider:
    def __init__(self, model_name: str, dimension: int):
        from langchain_openai import OpenAIEmbeddings
        from core.config import settings
        self._model_name = model_name
        self._dimension = dimension
        self._embeddings = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=settings.OPENAI_API_KEY
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._embeddings.aembed_documents(texts)

    async def embed_query(self, text: str) -> List[float]:
        return await self._embeddings.aembed_query(text)
