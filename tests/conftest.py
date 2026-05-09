from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from app.infrastructure.embedding_store import EmbeddingStore
from app.infrastructure.spatial_diff import SpatialDiff

FIXTURES_DIR = Path(__file__).parent / "fixtures"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
IMAGES_DIR = FIXTURES_DIR / "images"


def _cuda_available() -> bool:
    import torch

    return torch.cuda.is_available()


# ── GPU marker ────────────────────────────────────────────────


def pytest_configure(config):
    config.addinivalue_line("markers", "gpu: requires CUDA GPU to run")


def pytest_collection_modifyitems(config, items):
    if _cuda_available():
        return
    skip_gpu = pytest.mark.skip(reason="CUDA not available")
    for item in items:
        if "gpu" in item.keywords:
            item.add_marker(skip_gpu)


# ── Unit test fixtures ────────────────────────────────────────


@pytest.fixture
def random_image() -> Image.Image:
    arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    return Image.fromarray(arr)


@pytest.fixture
def random_embedding() -> torch.Tensor:
    return torch.randn(1280)


@pytest.fixture
def random_tokens() -> torch.Tensor:
    return torch.randn(256, 1280)


@pytest.fixture
def store(tmp_path) -> EmbeddingStore:
    return EmbeddingStore(persist_path=str(tmp_path / "test_embeddings.pt"))


@pytest.fixture
def spatial_diff() -> SpatialDiff:
    return SpatialDiff()


# ── GPU integration fixtures ──────────────────────────────────


@pytest.fixture(scope="session")
def real_encoder():
    from app.infrastructure.ijepa_encoder import IjepaEncoder

    device = "cuda" if _cuda_available() else "cpu"
    enc = IjepaEncoder(device=device)
    # Store embed dim for test assertions
    with torch.no_grad():
        dummy = torch.randn(1, 3, 224, 224, device=device)
        out = enc._model(dummy)
        enc._embed_dim = out.last_hidden_state.shape[-1]
    return enc


@pytest.fixture
def fixture_images():
    if not MANIFEST_PATH.exists():
        pytest.skip("Fixture images not downloaded. Run scripts/download_fixtures.py")
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    by_category: dict[str, list[Image.Image]] = {}
    for entry in manifest:
        cat = entry["category"]
        img_path = FIXTURES_DIR / entry["image_path"]
        if img_path.exists():
            by_category.setdefault(cat, []).append(Image.open(img_path).convert("RGB"))
    if not by_category:
        pytest.skip("No fixture images found on disk")
    return by_category


@pytest.fixture
def real_store(tmp_path, real_encoder, fixture_images):
    store = EmbeddingStore(persist_path=str(tmp_path / "real_embeddings.pt"))
    from app.application.use_cases.verify_helpers import compute_baseline

    for cat, images in fixture_images.items():
        for i, img in enumerate(images[:2]):  # ingest first 2 per category
            pid = f"{cat}_{i:03d}"
            emb = real_encoder.encode_image(img)
            store.put(pid, emb)
            baseline = compute_baseline(real_encoder, emb.numpy(), img)
            store.put_baseline(pid, baseline.model_dump())
    store.save()
    return store
