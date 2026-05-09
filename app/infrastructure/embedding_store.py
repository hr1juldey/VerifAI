from __future__ import annotations

import logging
from pathlib import Path

import torch

from app.application.ports import EmbeddingStorePort
from app.domain.value_objects import ProductId

logger = logging.getLogger(__name__)


def _migrate_legacy(store: dict) -> dict[str, dict]:
    migrated: dict[str, dict] = {}
    for pid, val in store.items():
        if isinstance(val, torch.Tensor):
            migrated[pid] = {"embedding": val, "baseline": None}
        else:
            migrated[pid] = val
    return migrated


class EmbeddingStore(EmbeddingStorePort):
    def __init__(self, persist_path: str = "data/embeddings.pt") -> None:
        self._store: dict[str, dict] = {}
        self._path = Path(persist_path)

    def get(self, product_id: ProductId) -> torch.Tensor | None:
        entry = self._store.get(product_id)
        return entry["embedding"] if entry else None

    def put(self, product_id: ProductId, embedding: torch.Tensor) -> None:
        existing = self._store.get(product_id, {})
        self._store[product_id] = {**existing, "embedding": embedding}

    def get_baseline(self, product_id: ProductId) -> dict | None:
        entry = self._store.get(product_id)
        return entry.get("baseline") if entry else None

    def put_baseline(self, product_id: ProductId, baseline: dict) -> None:
        existing = self._store.get(product_id, {})
        self._store[product_id] = {**existing, "baseline": baseline}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self._store, self._path)
        logger.info("saved %d embeddings to %s", len(self._store), self._path)

    def load(self) -> None:
        if self._path.exists():
            raw = torch.load(self._path, weights_only=False)
            self._store = _migrate_legacy(raw)
            logger.info("loaded %d embeddings from %s", len(self._store), self._path)

    def size(self) -> int:
        return len(self._store)

    def memory_estimate_mb(self) -> float:
        total = 0.0
        for entry in self._store.values():
            emb = entry.get("embedding")
            if emb is not None:
                total += emb.nelement() * emb.element_size()
        return total / 1e6
