from __future__ import annotations

import pytest
import torch
from PIL import Image
import numpy as np

from app.infrastructure.embedding_store import EmbeddingStore
from app.infrastructure.spatial_diff import SpatialDiff


@pytest.fixture
def random_image() -> Image.Image:
    arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    return Image.fromarray(arr)


@pytest.fixture
def random_embedding() -> torch.Tensor:
    return torch.randn(1024)


@pytest.fixture
def random_tokens() -> torch.Tensor:
    return torch.randn(256, 1024)


@pytest.fixture
def store(tmp_path) -> EmbeddingStore:
    return EmbeddingStore(persist_path=str(tmp_path / "test_embeddings.pt"))


@pytest.fixture
def spatial_diff() -> SpatialDiff:
    return SpatialDiff()
