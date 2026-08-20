import asyncio
from typing import List
import numpy as np

class LocalEmbeddingProvider:
    def __init__(self, model_name: str, dimension: int):
        self._model_name = model_name
        self._dimension = dimension
        self._model = None # Lazy load

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _embed_documents_sync(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        # encode returns numpy array or list of tensors depending on args
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [e.tolist() for e in embeddings]

    def _embed_query_sync(self, text: str) -> List[float]:
        model = self._get_model()
        embedding = model.encode(text, show_progress_bar=False)
        if isinstance(embedding, np.ndarray):
            return embedding.tolist()
        return embedding.tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._embed_documents_sync, texts)

    async def embed_query(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._embed_query_sync, text)
