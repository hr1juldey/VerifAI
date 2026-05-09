## 1. Domain Layer — Entities and Value Objects

- [x] 1.1 Create `app/domain/entities.py` — define `VerificationResult` (decision, confidence, latency_ms, spatial_diff_image, explanation), `Embedding` (tensor, product_id), `SpatialDiffMap` (heatmap array, annotated_image)
- [x] 1.2 Create `app/domain/value_objects.py` — define `ProductId` (str), `MatchScore` (float with threshold comparison), `ImageData` (PIL Image or numpy array)

## 2. Application Layer — Ports and Use Cases

- [x] 2.1 Create `app/application/ports.py` — define abstract interfaces: `EncoderPort` (encode_image, encode_batch), `EmbeddingStorePort` (get, put, save, load), `ExplainerPort` (explain), `SpatialDiffPort` (compute_diff, render_overlay, create_composite)
- [x] 2.2 Create `app/application/use_cases/ingest_catalog.py` — use case that accepts product_id + image, calls encoder to get global embedding, stores in cache, returns confirmation
- [x] 2.3 Create `app/application/use_cases/verify_return.py` — use case that accepts return image + product_id, retrieves catalog embedding, runs encoder on return image, computes global cosine similarity, returns MATCH/REJECT; on REJECT triggers spatial diff + explainer
- [x] 2.4 Create `app/application/use_cases/explain_rejection.py` — use case that accepts catalog image + annotated return image + product description, constructs constrained prompt, calls explainer port, returns cleaned explanation string

## 3. Infrastructure Layer — I-JEPA Encoder

- [x] 3.1 Create `app/infrastructure/ijepa_encoder.py` — load `facebook/ijepa_vith14_22k` via AutoModel, convert to FP16, implement `EncoderPort`; single-image and batch inference; return both global (mean-pooled) and per-token embeddings
- [x] 3.2 Add model loading to FastAPI lifespan in `app/presentation/main.py` — load model at startup, store in app.state, log VRAM usage and model metadata

## 4. Infrastructure Layer — Spatial Diff

- [x] 4.1 Create `app/infrastructure/spatial_diff.py` — compute per-token cosine similarity [256], reshape to [16,16], bilinear upscale to image dimensions, apply red/orange colormap with alpha blending via OpenCV, implement `SpatialDiffPort`
- [x] 4.2 Add composite image generation — concatenate catalog + annotated return horizontally for Gemma 4 input

## 5. Infrastructure Layer — Embedding Cache

- [x] 5.1 Create `app/infrastructure/embedding_store.py` — in-memory dict[product_id, tensor], implement `EmbeddingStorePort`; save/load to .pt file; report cache size and memory estimate

## 6. Infrastructure Layer — Gemma 4 Explainer

- [x] 6.1 Create `app/infrastructure/gemma_explainer.py` — DSPy module with `ExplainRejection` signature (catalog_image: dspy.Image, return_image: dspy.Image, product_description: str → explanation: str); initialize `dspy.LM("ollama_chat/gemma4:e4b", api_base="http://localhost:11434", api_key="")` at startup using local gemma4:e4b model; implement `ExplainerPort`; strip markdown/preamble from response

## 7. Presentation Layer — API Routes

- [x] 7.1 Create `app/presentation/schemas.py` — Pydantic models: VerifyRequest, VerifyResponse, CatalogRequest, CatalogResponse, HealthResponse
- [x] 7.2 Create `app/presentation/routes/health.py` — GET /health returning GPU status, I-JEPA model loaded, cache size, DSPy LM provider (ollama_chat/gemma4:e4b) and Ollama connectivity
- [x] 7.3 Create `app/presentation/routes/catalog.py` — POST /catalog accepting multipart image + product_id, calling ingest_catalog use case
- [x] 7.4 Create `app/presentation/routes/verify.py` — POST /verify accepting multipart image + product_id, calling verify_return use case, async with semaphore(2) for GPU concurrency
- [x] 7.5 Create `app/presentation/main.py` — FastAPI app factory, lifespan handler for model + cache loading, include all routers, configure CORS, read VERIFICATION_THRESHOLD from env

## 8. Integration and Smoke Test

- [x] 8.1 Create `tests/conftest.py` — pytest fixtures for mock encoder, mock store, test images (use random tensors), test client
- [x] 8.2 Create `tests/test_verify_pipeline.py` — test MATCH case (high similarity), test REJECT case (low similarity triggers spatial diff + DSPy explainer), test 404 for unknown product_id; mock DSPy LM for deterministic testing
- [x] 8.3 Create `tests/test_spatial_diff.py` — test per-token cosine computation, test heatmap reshape and upscale, test overlay rendering, test composite generation
- [x] 8.4 Run `ruff check --fix` and `ruff format` on all files, verify zero violations
