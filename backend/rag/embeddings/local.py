import asyncio
from typing import List
import numpy as np

_MODEL_CACHE = {}

class LocalEmbeddingProvider:
    def __init__(self, model_name: str, dimension: int):
        self._model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_model(self):
        if self._model_name not in _MODEL_CACHE:
            import os
            from loguru import logger
            try:
                import torch
                torch.set_num_threads(2)
            except Exception:
                pass
            from sentence_transformers import SentenceTransformer
            
            # Check for direct local model directory in /app/models or relative
            model_basename = os.path.basename(self._model_name)
            local_paths = [
                f"/app/models/{model_basename}",
                f"./models/{model_basename}",
                f"models/{model_basename}",
            ]
            loaded = False
            for p in local_paths:
                if os.path.isdir(p) and os.path.exists(os.path.join(p, "config.json")):
                    logger.info(f"Loading SentenceTransformer directly from local path: {p}")
                    _MODEL_CACHE[self._model_name] = SentenceTransformer(p)
                    loaded = True
                    break
            
            if not loaded:
                _MODEL_CACHE[self._model_name] = SentenceTransformer(self._model_name)
        return _MODEL_CACHE[self._model_name]

    def _embed_documents_sync(self, texts: List[str]) -> List[List[float]]:
        import torch
        model = self._get_model()
        with torch.inference_mode():
            embeddings = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [e.tolist() for e in embeddings]

    def _embed_query_sync(self, text: str) -> List[float]:
        import torch
        model = self._get_model()
        with torch.inference_mode():
            embedding = model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        if isinstance(embedding, np.ndarray):
            return embedding.tolist()
        return embedding.tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._embed_documents_sync, texts)

    async def embed_query(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._embed_query_sync, text)
