## Why

The current tests for the SUSPECT decision path use random tensors that produce meaningless cosine similarities. Random noise doesn't represent real product images — spatial diff, baseline computation, and augmentation consistency all produce garbage numbers when fed random embeddings. The tests pass or fail based on tensor arithmetic luck, not on whether the pipeline works on real visual data.

The VerifAI pipeline specifically targets Indian D2C e-commerce — sarees, kurtas, sherwanis, lehengas. Testing with random tensors tells us nothing about how the system handles zari work, bandhani patterns, or hand-embroidery variation. We need real product images flowing through the real I-JEPA encoder.

Additionally, there is no dev-server setup. The FastAPI app has no hot reload, no structured logging to file, and no tmux-based workflow for iterative development.

## What

### New capability: `integration-test-fixtures`

Download 40 real product images from the `validmodel/indo-fashion-dataset` Kaggle dataset (106K images, 15 Indian ethnic categories with JSON metadata). Select 10 images each from 4 categories: saree, kurta, sherwani, lehenga. Store as test fixtures in `tests/fixtures/images/` with a `manifest.json` mapping image paths to metadata (category, brand, product_title).

Rewrite all suspect-path tests to load real images, encode through the actual I-JEPA encoder, and verify pipeline behavior with realistic embeddings. Add a pytest marker `@pytest.mark.gpu` to gate GPU-dependent tests.

### New capability: `dev-server-workflow`

Configure uvicorn with `--reload --reload-dir app/` (watchfiles already installed via uvicorn[standard]). Add a `log_config.json` for structured logging to `verifai.log` in repo root. Create a `scripts/dev.sh` that launches a tmux session with two panes: server (hot reload) and a shell for running tests.

## Scope

- Add `kagglehub` and `kagglehub[pandas-datasets]` to requirements.txt
- Download fixture images via kagglehub (one-time script)
- Create `tests/fixtures/` directory with images and manifest
- Rewrite `tests/test_suspect_path.py` to use real images + real encoder
- Add `log_config.json` for file + console logging
- Add `verifai.log` to `.gitignore`
- Create `scripts/dev.sh` for tmux dev workflow
- Update `.env.example` with `LOG_CONFIG_PATH`
