from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
import torch

from app.domain.entities import ProductBaseline
from app.infrastructure.embedding_store import EmbeddingStore, _migrate_legacy
from app.infrastructure.spatial_diff import SpatialDiff


# ── 8.1 Per-product baseline computation ──────────────────────


def test_compute_baseline(random_image):
    from app.application.use_cases.verify_helpers import compute_baseline

    catalog_emb = np.ones(1024, dtype=np.float32)
    catalog_emb /= np.linalg.norm(catalog_emb)
    catalog_t = torch.from_numpy(catalog_emb)

    # 5 embeddings ~0.85 cosine sim to catalog
    fake_batch = torch.stack(
        [catalog_t * 0.85 + torch.randn(1024) * 0.1 for _ in range(5)]
    )

    encoder = MagicMock()
    encoder.encode_batch.return_value = fake_batch

    baseline = compute_baseline(encoder, catalog_emb, random_image)

    assert isinstance(baseline, ProductBaseline)
    assert 0.5 <= baseline.mean <= 1.0
    assert baseline.std >= 0.0
    assert baseline.min <= baseline.mean
    assert baseline.threshold == pytest.approx(baseline.mean - 2 * baseline.std, abs=1e-6)
    assert baseline.regional_threshold == pytest.approx(baseline.min - 0.05, abs=1e-6)
    assert baseline.delta_threshold == 0.15
    encoder.encode_batch.assert_called_once()


# ── 8.2 SUSPECT decision path ─────────────────────────────────


@pytest.mark.asyncio
async def test_suspect_decision_path():
    from app.application.use_cases.verify_return import VerifyReturnUseCase

    encoder = MagicMock()
    store = MagicMock()
    spatial = SpatialDiff()
    explainer = AsyncMock()

    # Setup: catalog embedding exists with baseline
    catalog_emb = torch.randn(1024)
    store.get.return_value = catalog_emb
    store.get_baseline.return_value = {
        "mean": 0.9,
        "std": 0.04,
        "min": 0.82,
        "threshold": 0.82,
        "regional_threshold": 0.77,
        "delta_threshold": 0.15,
    }

    # Return embedding close to catalog (passes global threshold)
    return_emb = catalog_emb + torch.randn(1024) * 0.05
    return_emb = return_emb / return_emb.norm() * catalog_emb.norm()

    # Tokens: catalog vs return with regional differences
    catalog_tokens = torch.randn(256, 1024)
    return_tokens = catalog_tokens.clone()
    # Make 3 contiguous patches very different (rows 4, cols 6-8)
    return_tokens[4 * 16 + 6] = torch.randn(1024) * 3
    return_tokens[4 * 16 + 7] = torch.randn(1024) * 3
    return_tokens[4 * 16 + 8] = torch.randn(1024) * 3

    # norm_tokens: same as return_tokens (no improvement → CONTENT_DIFF)
    norm_tokens = return_tokens.clone()

    encoder.encode_image.side_effect = [
        (return_emb, return_tokens),  # return image
        (torch.randn(1024), catalog_tokens),  # catalog image
        (torch.randn(1024), norm_tokens),  # CLAHE re-encode
    ]

    explainer.explain.return_value = ("CONTENT_DIFF", "Different logo proportions")
    store.get_baseline.return_value["delta_threshold"] = 0.15

    uc = VerifyReturnUseCase(encoder, store, spatial, explainer, threshold=0.7)
    img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

    result = await uc.execute("SKU-001", img, img)

    assert result.decision in ("SUSPECT", "REJECT", "MATCH")
    assert result.product_id == "SKU-001"


# ── 8.3 Augmentation consistency — LIGHTING_ARTIFACT ──────────


@pytest.mark.asyncio
async def test_lighting_artifact_resolution():
    from app.application.use_cases.verify_return import VerifyReturnUseCase

    encoder = MagicMock()
    store = MagicMock()
    spatial = SpatialDiff()
    explainer = AsyncMock()

    catalog_emb = torch.ones(1024)
    catalog_emb = catalog_emb / catalog_emb.norm()
    store.get.return_value = catalog_emb
    store.get_baseline.return_value = {
        "mean": 0.9,
        "std": 0.04,
        "min": 0.82,
        "threshold": 0.60,
        "regional_threshold": 0.10,
        "delta_threshold": 0.15,
    }

    return_emb = catalog_emb * 0.98

    # Catalog tokens: unit vectors for clean baseline
    catalog_tokens = torch.randn(256, 1024)
    catalog_tokens = catalog_tokens / catalog_tokens.norm(dim=-1, keepdim=True)

    # Return tokens: mostly same, but 3 contiguous patches are very different
    return_tokens = catalog_tokens.clone()
    for idx in [70, 71, 72]:  # row 4, cols 6-8
        return_tokens[idx] = torch.randn(1024)
        return_tokens[idx] = return_tokens[idx] / return_tokens[idx].norm()

    # CLAHE norm_tokens: back to catalog (lighting fixed)
    norm_tokens = catalog_tokens.clone()

    encoder.encode_image.side_effect = [
        (return_emb, return_tokens),
        (torch.randn(1024), catalog_tokens),
        (torch.randn(1024), norm_tokens),
    ]

    uc = VerifyReturnUseCase(encoder, store, spatial, explainer, threshold=0.7)
    img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    result = await uc.execute("SKU-001", img, img)

    assert result.decision == "MATCH"
    assert result.suspect_reason == "LIGHTING_ARTIFACT"


# ── 8.4 Legacy embedding store compatibility ──────────────────


def test_legacy_store_compatibility(tmp_path):
    path = tmp_path / "legacy.pt"
    # Old format: dict[str, Tensor]
    old_data = {"SKU-001": torch.randn(1024), "SKU-002": torch.randn(1024)}
    torch.save(old_data, path)

    store = EmbeddingStore(persist_path=str(path))
    store.load()

    assert store.get("SKU-001") is not None
    assert store.get("SKU-002") is not None
    assert store.get_baseline("SKU-001") is None
    assert store.get_baseline("SKU-002") is None

    # Verify tensors are preserved
    assert torch.equal(store.get("SKU-001"), old_data["SKU-001"])


def test_migrate_legacy():
    old = {"A": torch.randn(128), "B": torch.randn(256)}
    migrated = _migrate_legacy(old)
    assert isinstance(migrated["A"], dict)
    assert "embedding" in migrated["A"]
    assert "baseline" in migrated["A"]
    assert migrated["A"]["baseline"] is None
    assert torch.equal(migrated["A"]["embedding"], old["A"])


def test_new_format_round_trip(tmp_path):
    path = tmp_path / "new.pt"
    store = EmbeddingStore(persist_path=str(path))
    emb = torch.randn(1024)
    store.put("SKU-001", emb)
    baseline = ProductBaseline(
        mean=0.88,
        std=0.04,
        min=0.82,
        threshold=0.80,
        regional_threshold=0.77,
        delta_threshold=0.15,
    )
    store.put_baseline("SKU-001", baseline.model_dump())
    store.save()

    store2 = EmbeddingStore(persist_path=str(path))
    store2.load()
    assert torch.equal(store2.get("SKU-001"), emb)
    bl = store2.get_baseline("SKU-001")
    assert bl is not None
    assert bl["mean"] == 0.88
    assert bl["threshold"] == 0.80


# ── 8.5 Calibration endpoint ─────────────────────────────────


def test_calibration_jsonl(tmp_path):
    from app.presentation.routes.calibrate import post_calibrate
    from app.presentation.schemas import CalibrateRequest

    import os

    cal_path = tmp_path / "cal.jsonl"
    os.environ["CALIBRATION_PATH"] = str(cal_path)

    req = CalibrateRequest(
        product_id="SKU-001",
        category="saree",
        decision="SUSPECT",
        human_label="genuine",
        cosine_sim=0.71,
    )
    import asyncio

    result = asyncio.get_event_loop().run_until_complete(post_calibrate(req))
    assert result.status == "recorded"

    with open(cal_path) as f:
        entry = json.loads(f.readline())
    assert entry["product_id"] == "SKU-001"
    assert entry["category"] == "saree"
    assert entry["human_label"] == "genuine"


def test_calibration_stats(tmp_path):
    from app.presentation.routes.calibrate import get_calibration_stats

    import os

    cal_path = tmp_path / "stats.jsonl"
    os.environ["CALIBRATION_PATH"] = str(cal_path)

    entries = [
        {
            "product_id": "S1",
            "category": "saree",
            "decision": "SUSPECT",
            "human_label": "genuine",
            "cosine_sim": 0.71,
        },
        {
            "product_id": "S2",
            "category": "saree",
            "decision": "MATCH",
            "human_label": "counterfeit",
            "cosine_sim": 0.90,
        },
        {
            "product_id": "S3",
            "category": "saree",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.88,
        },
        {
            "product_id": "K1",
            "category": "kurta",
            "decision": "REJECT",
            "human_label": "counterfeit",
            "cosine_sim": 0.55,
        },
        {
            "product_id": "K2",
            "category": "kurta",
            "decision": "SUSPECT",
            "human_label": "genuine",
            "cosine_sim": 0.74,
        },
        {
            "product_id": "K3",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.85,
        },
        {
            "product_id": "K4",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "counterfeit",
            "cosine_sim": 0.82,
        },
        {
            "product_id": "K5",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.91,
        },
        {
            "product_id": "K6",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.87,
        },
        {
            "product_id": "K7",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.89,
        },
        {
            "product_id": "K8",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.90,
        },
        {
            "product_id": "K9",
            "category": "kurta",
            "decision": "SUSPECT",
            "human_label": "genuine",
            "cosine_sim": 0.76,
        },
        {
            "product_id": "K10",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.88,
        },
        {
            "product_id": "K11",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.92,
        },
        {
            "product_id": "K12",
            "category": "kurta",
            "decision": "REJECT",
            "human_label": "counterfeit",
            "cosine_sim": 0.50,
        },
        {
            "product_id": "K13",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.93,
        },
        {
            "product_id": "K14",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.86,
        },
        {
            "product_id": "K15",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.88,
        },
        {
            "product_id": "K16",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.91,
        },
        {
            "product_id": "K17",
            "category": "kurta",
            "decision": "MATCH",
            "human_label": "genuine",
            "cosine_sim": 0.87,
        },
    ]
    with open(cal_path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    import asyncio

    result = asyncio.get_event_loop().run_until_complete(get_calibration_stats())

    # saree: 3 total, 1 false_flag (SUSPECT+genuine), 1 false_pass (MATCH+counterfeit)
    assert result.categories is not None
    saree = result.categories["saree"]
    assert saree["total"] == 3
    assert saree["type1_rate"] == pytest.approx(1 / 3, abs=0.01)
    assert saree["type2_rate"] == pytest.approx(1 / 3, abs=0.01)

    # kurta: 17 total, 2 false_flag, 1 false_pass
    kurta = result.categories["kurta"]
    assert kurta["total"] == 17
    assert kurta["type1_rate"] == pytest.approx(2 / 17, abs=0.01)
    assert kurta["type2_rate"] == pytest.approx(1 / 17, abs=0.01)
