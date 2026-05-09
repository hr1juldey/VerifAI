## 1. Domain Layer — New Entities

- [ ] 1.1 Create `app/domain/entities.py` additions — add `ProductBaseline` Pydantic model with fields: mean, std, min, threshold, regional_threshold, delta_threshold (all float)
- [ ] 1.2 Create `app/domain/value_objects.py` additions — add `SuspectReason` str enum (LIGHTING_ARTIFACT, CONTENT_DIFF) and `Decision` str enum (MATCH, SUSPECT, REJECT)

## 2. Embedding Store — Baseline Storage

- [ ] 2.1 Modify `app/infrastructure/embedding_store.py` — change internal store from `dict[str, Tensor]` to `dict[str, dict]` with keys "embedding" and "baseline"; add `get_baseline(product_id)` method; maintain backward compatibility for legacy .pt files
- [ ] 2.2 Update `app/application/ports.py` — add `get_baseline`, `put_baseline` methods to `EmbeddingStorePort`

## 3. I-JEPA Encoder — Batch + CLAHE

- [ ] 3.1 Add `encode_batch` method to `app/infrastructure/ijepa_encoder.py` — accept list of images, return tensor of shape [N, 1024]; stack inputs for single forward pass
- [ ] 3.2 Add `normalize_clahe` utility function to `app/infrastructure/ijepa_encoder.py` — apply CLAHE per-channel via OpenCV, return normalized image

## 4. Spatial Diff — Regional Threshold + Delta

- [ ] 4.1 Modify `app/infrastructure/spatial_diff.py` compute_diff — accept optional regional_threshold param; return flagged_count and contiguous_regions count alongside SpatialDiffMap
- [ ] 4.2 Add `compute_patch_deltas` function to `app/infrastructure/spatial_diff.py` — given raw_tokens, norm_tokens, catalog_tokens, compute per-patch cosine delta between raw and normalized encodings

## 5. Gemma Explainer — Structured Output

- [ ] 5.1 Modify `app/infrastructure/gemma_explainer.py` — add `verdict` field to ExplainRejection DSPy signature as `dspy.OutputField(desc="One of: LIGHTING_ARTIFACT or CONTENT_DIFF")`; update predictor to return both verdict and explanation

## 6. Suspect Path — Use Case

- [ ] 6.1 Create `app/application/use_cases/verify_helpers.py` additions — add `compute_baseline` function that generates 5 augmented variants (brightness, blur, shadow, color shift, rotation) and returns ProductBaseline
- [ ] 6.2 Modify `app/application/use_cases/ingest_catalog.py` — call compute_baseline after encoding catalog image, store baseline alongside embedding
- [ ] 6.3 Modify `app/application/use_cases/verify_return.py` — implement three-way decision: load per-product baseline (or global fallback), check global cosine, check spatial diff regional thresholds, trigger augmentation consistency test on SUSPECT, resolve LIGHTING_ARTIFACT vs CONTENT_DIFF

## 7. Presentation Layer — API Updates

- [ ] 7.1 Modify `app/presentation/schemas.py` — add decision enum (MATCH/SUSPECT/REJECT), suspect_reason field, baseline_threshold field to VerifyResponse
- [ ] 7.2 Modify `app/presentation/routes/verify.py` — pass per-product baseline to use case, include new fields in response
- [ ] 7.3 Create `app/presentation/routes/calibrate.py` — POST /calibrate endpoint accepting product_id, category, decision, human_label, cosine_sim; append to JSONL file
- [ ] 7.4 Add GET /calibration/stats endpoint to calibrate.py — read JSONL, compute per-category Type 1/Type 2 rates
- [ ] 7.5 Modify `app/presentation/main.py` — include calibrate router, add CALIBRATION_PATH env var to .env.example

## 8. Tests

- [ ] 8.1 Add test for per-product baseline computation — verify baseline stats derived from augmented encodings
- [ ] 8.2 Add test for SUSPECT decision path — global sim passes but regional patches flag, verify SUSPECT returned
- [ ] 8.3 Add test for augmentation consistency — mock CLAHE re-encode with different similarity, verify LIGHTING_ARTIFACT resolution
- [ ] 8.4 Add test for legacy embedding store compatibility — load old .pt format, verify fallback to global defaults
- [ ] 8.5 Add test for calibration endpoint — POST a review label, verify JSONL entry, GET stats verify per-category rates
- [ ] 8.6 Run `ruff check --fix` and `ruff format` on all modified files
