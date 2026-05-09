from __future__ import annotations

import logging
from pathlib import Path

import torch

from app.application.ports import EmbeddingStorePort
from app.domain.value_objects import ProductId

logger = logging.getLogger(__name__)


class EmbeddingStore(EmbeddingStorePort):
    def __init__(self, persist_path: str = "data/embeddings.pt") -> None:
        self._store: dict[str, torch.Tensor] = {}
        self._path = Path(persist_path)

    def get(self, product_id: ProductId) -> torch.Tensor | None:
        return self._store.get(product_id)

    def put(self, product_id: ProductId, embedding: torch.Tensor) -> None:
        self._store[product_id] = embedding

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self._store, self._path)
        logger.info("saved %d embeddings to %s", len(self._store), self._path)

    def load(self) -> None:
        if self._path.exists():
            self._store = torch.load(self._path, weights_only=False)
            logger.info("loaded %d embeddings from %s", len(self._store), self._path)

    def size(self) -> int:
        return len(self._store)

    def memory_estimate_mb(self) -> float:
        total = sum(t.nelement() * t.element_size() for t in self._store.values())
        return total / 1e6
