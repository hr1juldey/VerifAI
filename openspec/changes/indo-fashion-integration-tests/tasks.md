## 1. Dependencies & Setup

- [x] 1.1 Add `kagglehub` and `kagglehub[pandas-datasets]` to `requirements.txt`
- [x] 1.2 Install kagglehub via `uv pip install kagglehub kagglehub[pandas-datasets]`

## 2. Fixture Download Script

- [x] 2.1 Create `scripts/download_fixtures.py` — download `validmodel/indo-fashion-dataset` via kagglehub, select 10 images each from saree, kurta, sherwani, lehenga (40 total), copy to `tests/fixtures/images/`, generate `tests/fixtures/manifest.json` with {image_path, category, brand, product_title, class_label} per image
- [x] 2.2 Run `scripts/download_fixtures.py` to populate `tests/fixtures/`
- [x] 2.3 Verify `tests/fixtures/manifest.json` has 40 entries and all images exist on disk

## 3. Test Infrastructure

- [x] 3.1 Add `@pytest.mark.gpu` marker to `conftest.py` and register it in `pyproject.toml`
- [x] 3.2 Add `real_encoder` fixture to `conftest.py` — load actual IjepaEncoder on CUDA (or skip if no GPU)
- [x] 3.3 Add `fixture_images` fixture to `conftest.py` — load manifest.json, yield dict of {category: [PIL.Image]}
- [x] 3.4 Add `real_store` fixture to `conftest.py` — EmbeddingStore with tmp_path, pre-loaded with real embeddings

## 4. Integration Tests — Baseline & Encoding

- [x] 4.1 Rewrite `test_compute_baseline` to use real image + real encoder — verify mean >= 0.5, std >= 0.01, threshold = mean - 2*std
- [x] 4.2 Add `test_baseline_varies_by_category` — compute baselines for saree and sherwani, verify thresholds differ
- [x] 4.3 Add `test_encode_batch_real_images` — encode 5 fixture images, verify output shape [5, embed_dim], all norms > 0
- [x] 4.4 Add `test_normalize_clahe_real_image` — apply CLAHE to a real image, verify output shape preserved, re-encode produces valid 256xembed_dim tokens

## 5. Integration Tests — SUSPECT Path

- [x] 5.1 Rewrite `test_suspect_decision_path` — ingest real kurta image as catalog, submit different kurta as return, verify decision in (MATCH, SUSPECT, REJECT) with all fields populated
- [x] 5.2 Rewrite `test_lighting_artifact_resolution` — ingest real saree image, submit same image with synthetic shadow overlay, verify augmentation consistency test runs end-to-end
- [x] 5.3 Add `test_same_image_returns_match` — ingest catalog image, submit identical image, verify decision=MATCH and confidence > 0.95

## 6. Integration Tests — Store & Calibration

- [x] 7.1 Rewrite `test_legacy_store_compatibility` — save old format .pt with real embedding, load, verify migration
- [x] 7.2 Rewrite `test_new_format_round_trip` — store real embedding + baseline, save/load, verify round trip
- [x] 7.3 Rewrite `test_calibration_jsonl` and `test_calibration_stats` — use real category names from fixtures

## 7. Dev Server Workflow

- [x] 7.1 Create `log_config.json` in repo root — two handlers: console (colored) and file (structured JSON to `verifai.log`)
- [x] 7.2 Add `verifai.log` to `.gitignore`
- [x] 7.3 Add `LOG_CONFIG_PATH` to `.env.example`
- [x] 7.4 Create `scripts/dev.sh` — create tmux session `verifai` with pane 0 (uvicorn --reload --reload-dir app/ --log-config log_config.json) and pane 1 (bash shell)
- [x] 7.5 Verify dev server starts: run `scripts/dev.sh`, check tmux session has 2 panes, uvicorn shows "Application startup complete", kill session

## 8. Final Validation

- [x] 8.1 Run `uv run pytest -m "not gpu"` — verify all unit tests pass without GPU
- [x] 8.2 Run `uv run pytest -m gpu` — verify all GPU integration tests pass
- [x] 8.3 Run `uv run pytest` — verify all tests pass together
- [x] 8.4 Run `ruff check --fix` and `ruff format` on all modified files
