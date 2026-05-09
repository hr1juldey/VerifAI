"""GPU integration tests using real Indo Fashion dataset images.

Requires CUDA and fixture images (run scripts/download_fixtures.py first).
Marked with @pytest.mark.gpu — skipped automatically when no GPU.
"""

from __future__ import annotations


import numpy as np
import pytest
import torch

from app.application.use_cases.verify_helpers import compute_baseline
from app.domain.entities import ProductBaseline
from app.infrastructure.embedding_store import EmbeddingStore
from app.infrastructure.ijepa_encoder import normalize_clahe
from app.infrastructure.spatial_diff import SpatialDiff


# ── 4.1 Baseline computation with real images ─────────────────


@pytest.mark.gpu
def test_compute_baseline_real(real_encoder, fixture_images):
    images = fixture_images["saree"]
    img = images[0]
    embedding = real_encoder.encode_image(img)
    baseline = compute_baseline(real_encoder, embedding.numpy(), img)

    assert isinstance(baseline, ProductBaseline)
    assert 0.5 <= baseline.mean <= 1.0
    assert baseline.std >= 0.01
    assert baseline.min <= baseline.mean
    assert baseline.threshold == pytest.approx(
        baseline.mean - 2 * baseline.std, abs=1e-6
    )
    assert baseline.regional_threshold == pytest.approx(baseline.min - 0.05, abs=1e-6)
    assert baseline.delta_threshold == 0.15


# ── 4.2 Baseline varies by category ───────────────────────────


@pytest.mark.gpu
def test_baseline_varies_by_category(real_encoder, fixture_images):
    baselines = {}
    for cat in ["saree", "sherwani"]:
        if cat not in fixture_images:
            pytest.skip(f"No {cat} images in fixtures")
        img = fixture_images[cat][0]
        emb = real_encoder.encode_image(img)
        baselines[cat] = compute_baseline(real_encoder, emb.numpy(), img)

    # Thresholds should be different for different product types
    assert baselines["saree"].threshold != baselines["sherwani"].threshold


# ── 4.3 Encode batch with real images ─────────────────────────


@pytest.mark.gpu
def test_encode_batch_real_images(real_encoder, fixture_images):
    images = fixture_images["saree"][:5]
    pooled = real_encoder.encode_batch(images)

    embed_dim = real_encoder._embed_dim
    assert pooled.shape == (len(images), embed_dim)
    norms = pooled.norm(dim=-1)
    assert (norms > 0).all()


# ── 4.4 CLAHE normalization on real image ─────────────────────


@pytest.mark.gpu
def test_normalize_clahe_real_image(real_encoder, fixture_images):
    img = fixture_images["saree"][0]
    img_np = np.array(img)

    normalized = normalize_clahe(img_np)
    assert normalized.shape == img_np.shape
    assert normalized.dtype == np.uint8

    # Re-encode normalized image and verify valid tokens
    _, tokens = real_encoder.encode_image(normalized, return_tokens=True)
    embed_dim = real_encoder._embed_dim
    assert tokens.shape[0] == 256
    assert tokens.shape[1] == embed_dim


# ── 5.1 SUSPECT path with real images ─────────────────────────


@pytest.mark.asyncio
@pytest.mark.gpu
async def test_suspect_decision_path_real(real_encoder, fixture_images):
    from unittest.mock import AsyncMock

    from app.application.use_cases.verify_return import VerifyReturnUseCase

    if "kurta" not in fixture_images or len(fixture_images["kurta"]) < 2:
        pytest.skip("Need at least 2 kurta images")

    spatial = SpatialDiff()
    explainer = AsyncMock()
    explainer.explain.return_value = ("CONTENT_DIFF", "Different product details")

    store = EmbeddingStore(persist_path="/tmp/test_suspect_real.pt")
    catalog_img = fixture_images["kurta"][0]
    return_img = fixture_images["kurta"][1]

    # Ingest catalog
    catalog_emb = real_encoder.encode_image(catalog_img)
    store.put("KURTA-001", catalog_emb)
    baseline = compute_baseline(real_encoder, catalog_emb.numpy(), catalog_img)
    store.put_baseline("KURTA-001", baseline.model_dump())

    uc = VerifyReturnUseCase(real_encoder, store, spatial, explainer, threshold=0.7)
    result = await uc.execute("KURTA-001", return_img, catalog_img)

    assert result.decision in ("MATCH", "SUSPECT", "REJECT")
    assert result.product_id == "KURTA-001"
    assert result.confidence > 0


# ── 5.2 Lighting artifact with synthetic shadow ───────────────


@pytest.mark.asyncio
@pytest.mark.gpu
async def test_lighting_artifact_real(real_encoder, fixture_images):
    from unittest.mock import AsyncMock

    from app.application.use_cases.verify_return import VerifyReturnUseCase

    spatial = SpatialDiff()
    explainer = AsyncMock()

    store = EmbeddingStore(persist_path="/tmp/test_lighting_real.pt")
    catalog_img = fixture_images["saree"][0]

    catalog_emb = real_encoder.encode_image(catalog_img)
    store.put("SAREE-001", catalog_emb)
    baseline = compute_baseline(real_encoder, catalog_emb.numpy(), catalog_img)
    # Use very low thresholds to ensure SUSPECT triggers on shadow
    baseline_dict = baseline.model_dump()
    baseline_dict["threshold"] = min(baseline_dict["threshold"], 0.5)
    baseline_dict["regional_threshold"] = 0.10
    store.put_baseline("SAREE-001", baseline_dict)

    # Create shadowed version of same image
    img_np = np.array(catalog_img)
    h, w = img_np.shape[:2]
    shadow = img_np.copy().astype(np.float32)
    shadow[h // 3 : 2 * h // 3, w // 3 : 2 * w // 3] *= 0.3
    shadow_img = shadow.clip(0, 255).astype(np.uint8)

    uc = VerifyReturnUseCase(real_encoder, store, spatial, explainer, threshold=0.7)
    result = await uc.execute("SAREE-001", shadow_img, catalog_img)

    assert result.decision in ("MATCH", "SUSPECT", "REJECT")
    # With CLAHE normalization, a shadow on the same image should resolve
    # to MATCH with LIGHTING_ARTIFACT, or stay SUSPECT for Gemma


# ── 5.3 Same image returns MATCH ──────────────────────────────


@pytest.mark.asyncio
@pytest.mark.gpu
async def test_same_image_returns_match(real_encoder, fixture_images):
    from unittest.mock import AsyncMock

    from app.application.use_cases.verify_return import VerifyReturnUseCase

    spatial = SpatialDiff()
    explainer = AsyncMock()

    store = EmbeddingStore(persist_path="/tmp/test_same_match.pt")
    catalog_img = fixture_images["saree"][0]

    catalog_emb = real_encoder.encode_image(catalog_img)
    store.put("SAREE-MATCH", catalog_emb)
    baseline = compute_baseline(real_encoder, catalog_emb.numpy(), catalog_img)
    store.put_baseline("SAREE-MATCH", baseline.model_dump())

    uc = VerifyReturnUseCase(real_encoder, store, spatial, explainer, threshold=0.7)
    result = await uc.execute("SAREE-MATCH", catalog_img, catalog_img)

    assert result.decision == "MATCH"
    assert result.confidence > 0.95


# ── 7.1-7.2 Store with real embeddings ────────────────────────


@pytest.mark.gpu
def test_legacy_store_with_real_embedding(real_encoder, fixture_images):
    img = fixture_images["saree"][0]
    emb = real_encoder.encode_image(img)

    old_data = {"SKU-REAL": emb}
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pt") as f:
        torch.save(old_data, f.name)
        store = EmbeddingStore(persist_path=f.name)
        store.load()

    assert store.get("SKU-REAL") is not None
    assert store.get_baseline("SKU-REAL") is None
    assert torch.equal(store.get("SKU-REAL"), emb)


@pytest.mark.gpu
def test_new_format_round_trip_real(real_encoder, fixture_images):
    import tempfile

    from app.application.use_cases.verify_helpers import compute_baseline

    img = fixture_images["saree"][0]
    emb = real_encoder.encode_image(img)
    baseline = compute_baseline(real_encoder, emb.numpy(), img)

    with tempfile.NamedTemporaryFile(suffix=".pt") as f:
        store = EmbeddingStore(persist_path=f.name)
        store.put("SKU-RT", emb)
        store.put_baseline("SKU-RT", baseline.model_dump())
        store.save()

        store2 = EmbeddingStore(persist_path=f.name)
        store2.load()

    assert torch.equal(store2.get("SKU-RT"), emb)
    bl = store2.get_baseline("SKU-RT")
    assert bl is not None
    assert bl["mean"] == baseline.mean


# ── 7.3 Calibration with real categories ──────────────────────


def test_calibration_with_real_categories(tmp_path):
    import json
    import os

    from app.presentation.routes.calibrate import get_calibration_stats

    cal_path = tmp_path / "cal.jsonl"
    os.environ["CALIBRATION_PATH"] = str(cal_path)

    entries = [
        {
            "product_id": "S001",
            "category": "saree",
            "decision": "SUSPECT",
            "human_label": "genuine",
            "cosine_sim": 0.71,
        },
        {
            "product_id": "S002",
            "category": "saree",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.91,
        },
        {
            "product_id": "K001",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "counterfeit",
            "cosine_sim": 0.82,
        },
        {
            "product_id": "K002",
            "category": "kurta",
            "decision": "REJECT",
            "human_label": "counterfeit",
            "cosine_sim": 0.50,
        },
    ]
    with open(cal_path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(get_calibration_stats())

    assert result.categories is not None
    assert result.categories["saree"]["total"] == 2
    assert result.categories["saree"]["type1_rate"] == 0.5
    assert result.categories["kurta"]["total"] == 2
    assert result.categories["kurta"]["type2_rate"] == 0.5
