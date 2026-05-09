## Context

VerifAI's test suite has 16 tests, 4 of which currently fail because they use random tensors that don't produce meaningful cosine similarities. The SUSPECT decision path (CLAHE augmentation consistency, regional spatial diff, per-product baselines) cannot be meaningfully tested with noise — the math is technically correct but the semantics are meaningless.

The I-JEPA ViT-H/14 encoder is loaded on an RTX 3060 12GB. Encoding a single 224x224 image takes ~35ms. A batch of 5 takes ~40ms. 40 images through the full pipeline (encode + spatial diff + baseline) would take ~3 seconds total — acceptable for a test suite.

## Goals / Non-Goals

**Goals:**
- 40 real Indian fashion product images as test fixtures
- Real I-JEPA embeddings in all suspect-path tests
- Deterministic test results (same images → same embeddings → same thresholds)
- FastAPI dev server with hot reload and file logging
- Single-command tmux session for dev workflow

**Non-Goals:**
- Downloading the full 106K dataset (only 40 curated images)
- Training or fine-tuning on the dataset
- CI/CD GPU runner setup (these tests are local-only)
- Docker-based test environment

## Decisions

### D1: Fixture images over kagglehub API in tests

Download images once via a `scripts/download_fixtures.py` script. Store in `tests/fixtures/images/` with a `manifest.json`. Tests load from local disk — no network dependency at test time.

Alternative considered: Download via kagglehub at test time. Rejected because: (a) adds 10-30s to every test run, (b) requires Kaggle API credentials on every dev machine, (c) CI would need Kaggle auth.

### D2: 40 images across 4 categories

10 images per category: saree, kurta, sherwani, lehenga. These represent the highest-risk categories for Type 1/Type 2 errors (silk variation, hand-embroidery, zari work). 40 images × 2 encodes (catalog + return) = 80 forward passes ≈ 3 seconds.

### D3: pytest.mark.gpu marker

All real-image tests get `@pytest.mark.gpu`. This allows: `pytest -m "not gpu"` for fast unit tests, `pytest -m gpu` for integration tests. Default `pytest` runs everything.

### D4: Uvicorn hot reload with watchfiles

Already installed (`watchfiles==1.1.1` via `uvicorn[standard]`). Run with:
```
uvicorn app.presentation.main:app --reload --reload-dir app/ --log-config log_config.json
```

Watch only `app/` directory — not `tests/`, `data/`, or `openspec/`.

### D5: JSON log config with file + console handlers

Create `log_config.json` with two handlers:
1. `console` — colored output to stderr (existing behavior)
2. `file` — structured JSON lines to `verifai.log`

Application code already uses `logging.getLogger(__name__)` — no changes needed in app code.

### D6: tmux dev session via scripts/dev.sh

Single script creates a tmux session `verifai` with:
- Pane 0: `uvicorn` with hot reload (server)
- Pane 1: bash shell (for running tests, curl, etc.)

User attaches with `tmux attach -t verifai`.

## Risks / Trade-offs

**[GPU required for tests]** → Mitigation: `@pytest.mark.gpu` marker. CI can skip these. Local dev has RTX 3060.

**[3GB dataset download for script]** → Mitigation: Script downloads full dataset to kagglehub cache, then copies only 40 images to fixtures. Cache persists across runs.

**[Fixture images in git]** → Mitigation: 40 images at ~50KB each = ~2MB. Acceptable for git. Could add LFS later if needed.

**[Test non-determinism from I-JEPA]** → Mitigation: Encoder outputs are deterministic for same input (eval mode, no dropout). Tests will be reproducible.

## Migration Plan

1. Install kagglehub, run download_fixtures.py
2. Create log_config.json, add verifai.log to .gitignore
3. Rewrite test_suspect_path.py with real images
4. Create scripts/dev.sh
5. Verify all 16+ tests pass with `uv run pytest`
