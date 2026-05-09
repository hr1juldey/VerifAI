from __future__ import annotations

import pytest
import torch

from app.application.use_cases.ingest_catalog import IngestCatalogUseCase
from app.infrastructure.embedding_store import EmbeddingStore


@pytest.mark.asyncio
async def test_catalog_ingestion(store, random_image, random_embedding):
    from unittest.mock import MagicMock

    encoder = MagicMock()
    encoder.encode_image.return_value = random_embedding
    uc = IngestCatalogUseCase(encoder, store)
    result = await uc.execute("prod-001", random_image)
    assert result["product_id"] == "prod-001"
    assert result["embedding_dims"] == 1024
    assert store.get("prod-001") is not None


@pytest.mark.asyncio
async def test_catalog_reingestion_replaces(store, random_image, random_embedding):
    from unittest.mock import MagicMock

    encoder = MagicMock()
    encoder.encode_image.return_value = random_embedding
    uc = IngestCatalogUseCase(encoder, store)
    await uc.execute("prod-001", random_image)
    new_emb = torch.randn(1024)
    encoder.encode_image.return_value = new_emb
    await uc.execute("prod-001", random_image)
    assert torch.equal(store.get("prod-001"), new_emb)


def test_store_persistence(store, random_embedding, tmp_path):
    store.put("prod-001", random_embedding)
    store.save()
    store2 = EmbeddingStore(persist_path=str(tmp_path / "test_embeddings.pt"))
    store2.load()
    assert store2.size() == 1
    assert torch.equal(store2.get("prod-001"), random_embedding)


def test_store_missing_product(store):
    assert store.get("nonexistent") is None
