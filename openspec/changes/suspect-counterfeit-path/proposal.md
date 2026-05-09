## Why

The current binary MATCH/REJECT pipeline catches obvious mismatches (global cosine < 0.7) but misses counterfeits that look ~95% identical to the catalog image. Meanwhile, bad lighting on genuine returns causes false REJECTs — a customer's dim warehouse photo of a real product flags as different. Indian D2C faces both problems daily: counterfeit returns slip through (Type 2 underfitting) while genuine returns with shadow/flash artifacts get flagged (Type 1 overfitting). Per-category products (silk sarees, zari embroidery, hand-block prints) silently fail because a single global threshold cannot fit all product types (local misfitting).

## What Changes

- Add **SUSPECT** as a third decision between MATCH and REJECT, triggered when global cosine passes but regional spatial diffs show localized drops
- Add **per-product self-similarity baseline** computed at catalog ingestion: encode 5 augmented variants (lighting, blur, shadow, color shift, rotation) to derive product-specific mean/std threshold instead of one global 0.7
- Add **augmentation consistency test**: when spatial diff flags regions, re-encode the return image after CLAHE normalization and compare delta — large delta means lighting artifact (→MATCH), small delta means content difference (→SUSPECT/REJECT)
- Add **structured Gemma 4 output** for SUSPECT explanations: DSPy signature now returns `{verdict: CONTENT_DIFF|LIGHTING_ARTIFACT, explanation: str}` instead of raw text
- Add **calibration feedback endpoint** POST /calibrate accepting `{product_id, decision, human_label}` to close the loop on Type 1/Type 2 errors over time

## Capabilities

### New Capabilities
- `suspect-path`: SUSPECT decision logic, augmentation consistency test (CLAHE re-encode + delta comparison), per-product threshold derivation from self-similarity baseline
- `calibration-feedback`: POST /calibrate endpoint, human review label storage, per-category threshold drift detection

### Modified Capabilities
- `verification-api`: three-way decision (MATCH/SUSPECT/REJECT) instead of binary, structured response schema with `suspect_reason` field
- `gemma-explainer`: structured DSPy signature with `verdict` + `explanation` output fields, explicit lighting-vs-content distinction
- `ijepa-encoder`: batch encode with augmentation variants at catalog ingestion for self-similarity baseline
- `embedding-store`: store per-product baseline (mean, std, min, threshold) alongside catalog embedding
- `spatial-diff`: regional threshold parameter (per-product, not global)

## Impact

- **API**: POST /verify response gains `decision: MATCH|SUSPECT|REJECT` (was `MATCH|REJECT`), new `suspect_reason` field, new POST /calibrate endpoint
- **Latency**: SUSPECT path adds ~37ms (CLAHE + one extra I-JEPA forward pass) on ~5% of requests; MATCH/REJECT paths unchanged (~35ms)
- **Storage**: Per-product baseline is ~6 floats per product (mean, std, min, threshold, regional_threshold, delta_threshold) — negligible
- **Dependencies**: No new packages; uses existing OpenCV (CLAHE) and I-JEPA encoder
