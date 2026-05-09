## Context

VerifAI currently has a binary MATCH/REJECT pipeline. Global cosine similarity against a single threshold (0.7) decides the outcome. The spatial diff heatmap and Gemma 4 explainer only trigger on REJECT. This architecture has three failure modes: overfitting (genuine items flagged due to lighting), underfitting (counterfeits that are 95% similar pass through), and local misfitting (per-category products like silk sarees silently fail with a global threshold).

The existing system runs on a single RTX 3060 12GB with I-JEPA ViT-H/14 encoder, DSPy with Gemma 4 via Ollama, and an in-memory embedding cache persisted to .pt files.

## Goals / Non-Goals

**Goals:**
- Three-way decision: MATCH / SUSPECT / REJECT with clear triggering criteria
- Per-product self-similarity baseline replacing the global 0.7 threshold
- JEPA-native augmentation consistency test (CLAHE re-encode) to separate lighting from content
- Structured Gemma 4 output distinguishing LIGHTING_ARTIFACT from CONTENT_DIFF
- Calibration feedback loop for long-term per-category threshold tuning
- SUSPECT path latency under 100ms (Gemma explanation is optional, adds 600ms-2s)

**Non-Goals:**
- Fine-tuning I-JEPA on Indian product data (future)
- Loading the I-JEPA predictor network (future — would enable cross-image prediction)
- Automated threshold adjustment without human labels (future)
- Video or multi-angle verification (future)
- Frontend dashboard for calibration review (future)

## Decisions

### D1: Per-product self-similarity baseline over global threshold

At catalog ingestion, encode 5 augmented variants (random brightness/contrast, Gaussian blur, random shadow overlay, color temperature shift, small rotation). Compute mean/std/min of their cosine similarities against the catalog embedding. Product threshold = mean - 2*std. This gives a cotton t-shirt threshold of ~0.82 (low variation) and a hand-embroidered kurta threshold of ~0.68 (high variation), solving local misfitting.

Alternative considered: per-category thresholds from a config table. Rejected because it requires manual category mapping and doesn't capture within-category variation (two different sarees can have very different variation envelopes).

### D2: SUSPECT triggered by regional spatial diff, not global score

Even when global cosine passes the per-product threshold, check the 16x16 spatial diff map. If any contiguous region of 2+ patches exceeds the per-product regional threshold, trigger SUSPECT. This catches counterfeits that are globally similar but locally different (e.g., wrong logo proportions on a 95%-accurate fake shoe).

Regional threshold = product_baseline.min - 0.05 (slightly below the minimum variation seen during baseline calibration).

### D3: CLAHE augmentation consistency over SSIM or pixel comparison

When SUSPECT triggers, normalize the return image with CLAHE (Contrast Limited Adaptive Histogram Equalization) and re-encode. Compare delta between raw and normalized per-patch cosine similarities. Large delta (>0.15) means the difference was photometric (lighting/shadow). Small delta (<0.05) means the difference persists after normalization (actual content change).

CLAHE chosen over SSIM because Indian textiles (zari, bandhani, sheer fabrics) have high-frequency structural detail that SSIM penalizes as "structure changed." CLAHE normalizes local contrast without destroying pattern semantics. The comparison happens entirely in JEPA embedding space, not pixel space.

### D4: Structured DSPy signature with verdict field

The Gemma 4 explainer signature gains a `verdict` output field: `LIGHTING_ARTIFACT` or `CONTENT_DIFF`. This makes the SUSPECT resolution deterministic at the application level: if verdict is LIGHTING_ARTIFACT, override SUSPECT to MATCH. If CONTENT_DIFF, escalate to REJECT with explanation.

### D5: Calibration feedback as POST endpoint, not background job

Simple POST /calibrate endpoint accepting `{product_id, category, decision, human_label, cosine_sim}`. Stores to a JSONL file (one line per review). A separate CLI script reads the JSONL and computes per-category Type 1/Type 2 rates for manual threshold adjustment. Keeps the feedback loop simple and visible.

Alternative considered: automatic threshold adjustment via Bayesian optimization. Rejected for MVP — too risky to auto-adjust without human validation.

### D6: Embedding store schema change for baseline data

The .pt file cache currently stores `dict[product_id, tensor]`. Change to `dict[product_id, dict]` where each value is `{"embedding": tensor, "baseline": {"mean": float, "std": float, "min": float, "threshold": float, "regional_threshold": float, "delta_threshold": float}}`. Backward compatible: missing baseline falls back to global defaults.

## Risks / Trade-offs

**[Extra forward pass on SUSPECT]** → Mitigation: SUSPECT fires on ~5% of requests. The 37ms re-encode cost is acceptable. Weighted average latency stays near 36ms.

**[CLAHE may not normalize all lighting conditions]** → Mitigation: Extreme flash overexposure or complete darkness cannot be normalized. These cases remain SUSPECT and fall through to Gemma 4 for multimodal judgment.

**[Self-similarity baseline adds 200ms at ingestion]** → Mitigation: Catalog ingestion is not latency-sensitive (warehouse staff scanning products). 5 augmented encodes at ~35ms each is acceptable.

**[Baseline stored in memory limits scale]** → Mitigation: 6 floats per product is ~24 bytes. 100K products = ~2.4MB. Well within memory budget.

**[Structured Gemma output may not always be accurate]** → Mitigation: The augmentation consistency test (D3) provides a deterministic first pass. Gemma only judges when the deterministic test is ambiguous. Two layers of defense.

## Migration Plan

1. Deploy new code — embedding store loads old format (plain tensors) and treats them as "no baseline" (uses global defaults)
2. Re-ingest catalog to populate baselines (background job or lazy on next verify)
3. SUSPECT path activates immediately for new ingestions; falls back to MATCH/REJECT for legacy products
4. Calibration endpoint starts collecting labels from day one
5. After 2 weeks of labels, run calibration script to review per-category rates

## Open Questions

- Should the CLAHE delta threshold (0.15) be per-product or global? Need production data to decide.
- Should the calibration JSONL rotate/compact, or grow indefinitely for audit purposes?
