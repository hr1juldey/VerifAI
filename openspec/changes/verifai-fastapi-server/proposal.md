## Why

Indian D2C e-commerce loses ₹2,400+ crores/year (~$290M+) to return fraud — swap fraud, empty box returns, and counterfeits. Current solutions (manual packing videos, TrackVid) are labor-intensive and unscalable. No open, edge-deployable visual verification server exists that combines deterministic detection with human-readable claim evidence.

## What Changes

- New FastAPI server exposing a visual verification pipeline for product image matching
- I-JEPA (facebook/ijepa_vith14_22k, ViT-H/14, 632M params) as the deterministic detection backbone — cosine similarity on embeddings decides MATCH/REJECT
- Per-token spatial diff heatmap from I-JEPA's `last_hidden_state` — identifies WHERE the mismatch is, at zero extra compute cost (same forward pass)
- Gemma 4 multimodal (via Ollama) as a constrained explanation layer — only triggered on REJECT, grounded by spatial overlay + original catalog image to prevent hallucination
- Pre-computed embedding cache for catalog images — only return images need real-time inference
- Target hardware: RTX 3060 12GB, PASS latency ~35ms, REJECT with explanation ~600ms-2s

## Capabilities

### New Capabilities

- `ijepa-encoder`: Model loading, FP16 inference, global + per-token embedding extraction from I-JEPA ViT-H/14
- `spatial-diff`: Per-token cosine similarity computation, 16x16 heatmap generation, colormap overlay on original image
- `embedding-cache`: In-memory catalog embedding storage and lookup by product ID, with ingestion endpoint
- `verification-api`: FastAPI endpoints — POST /verify (main pipeline), POST /catalog (ingest catalog images), GET /health, async GPU concurrency via semaphore
- `gemma-explainer`: Ollama Gemma 4 integration — constrained prompt construction, anchored image formatting, natural language explanation output

### Modified Capabilities

(none — this is the first change)

## Impact

- **New files**: FastAPI application with clean architecture (domain/application/infrastructure/presentation layers)
- **Dependencies**: All already declared in pyproject.toml (torch, transformers, fastapi, opencv-python, scipy, pillow, uvicorn)
- **External dependency**: Ollama running locally with Gemma 4 multimodal model pulled
- **Hardware**: Requires CUDA-capable GPU with 12GB+ VRAM
- **No breaking changes**: Greenfield project
