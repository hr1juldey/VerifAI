## Context

VerifAI is a greenfield FastAPI server for visual verification of product returns in Indian D2C e-commerce. No code exists yet — only pyproject.toml with dependencies declared (torch, transformers, fastapi, opencv-python, scipy, pillow, uvicorn). The server must run on a single consumer GPU (RTX 3060 12GB) and produce both deterministic match decisions and human-readable claim evidence.

## Goals / Non-Goals

**Goals:**
- Deterministic MATCH/REJECT decisions via I-JEPA cosine similarity in ~35ms
- Spatial diff heatmap showing WHERE mismatches are, at zero extra compute
- Natural language explanations via Gemma 4 (Ollama) for rejected items only
- Pre-computed catalog embedding cache to avoid redundant inference
- Clean architecture obeying CLAUDE_POLICY.md: 100-line file limits, absolute imports, layer boundaries

**Non-Goals:**
- Federated learning or multi-warehouse sync (future)
- Frontend dashboard (future)
- Video processing / real-time camera streams (future)
- Fine-tuning I-JEPA on product data (using pretrained weights as-is)
- Authentication or multi-tenancy (single-tenant MVP)

## Decisions

### D1: Per-token cosine diff over Grad-CAM for spatial grounding

Per-token cosine similarity from `last_hidden_state` (shape [1, 256, 1024]) gives a lossless 16x16 spatial diff map in the same forward pass as the detection decision. Grad-CAM would require a backward pass and produce a noisier, gradient-filtered approximation of the same signal. The per-token approach is deterministic, free, and requires no gradient computation.

### D2: Gemma 4 constrained by spatial overlay, not raw comparison

Direct multimodal comparison ("what's different?") risks hallucination. Instead, the spatial diff overlay constrains Gemma 4's attention to flagged regions. The prompt explicitly instructs: "describe only what you see in the red-highlighted regions." Three anchors prevent ambiguity: the original catalog image, the overlay highlighting WHERE the diff is, and the constrained prompt.

### D3: In-memory embedding cache, no database for MVP

Catalog embeddings stored in a Python dict keyed by product_id. Persisted to disk as a .pt file on write. No Redis, no SQLite — the cache fits in memory (1000 products x 1024 floats x 4 bytes = ~4MB). This avoids infrastructure complexity for the MVP.

### D4: Async GPU concurrency via semaphore pattern

Following the Jonathan Chang pattern: `asyncio.Semaphore(2)` allows 2 concurrent requests to schedule GPU kernels while using `torch.cuda.Event()` + `non_blocking=True` to free the CPU. This maximizes GPU utilization without a task queue.

### D5: Directory structure following clean architecture

```
app/
├── domain/
│   └── entities.py              # VerificationResult, Embedding, SpatialDiffMap
├── application/
│   ├── use_cases/
│   │   ├── verify_return.py     # Main verification pipeline orchestration
│   │   ├── ingest_catalog.py    # Catalog embedding ingestion
│   │   └── explain_rejection.py # Gemma4 explanation construction
│   └── ports.py                 # Abstract interfaces for infrastructure
├── infrastructure/
│   ├── ijepa_encoder.py         # I-JEPA model loading + FP16 inference
│   ├── spatial_diff.py          # Per-token diff + colormap overlay
│   ├── embedding_store.py       # In-memory dict + .pt persistence
│   └── gemma_client.py          # Ollama HTTP client
└── presentation/
    ├── main.py                  # FastAPI app factory + lifespan
    ├── routes/
    │   ├── verify.py            # POST /verify
    │   ├── catalog.py           # POST /catalog
    │   └── health.py            # GET /health
    └── schemas.py               # Pydantic request/response models
```

Layer boundaries enforced per CLAUDE_POLICY.md Rule 1.2:
- domain → domain only
- application → domain
- infrastructure → domain, application
- presentation → application

### D6: I-JEPA model loaded once at startup, FP16

Model loaded in FastAPI lifespan handler, stored in app.state. FP16 conversion halves VRAM usage (~3GB vs ~6GB). The model stays on GPU for the lifetime of the process — no per-request loading.

## Risks / Trade-offs

- **I-JEPA vs DINOv2**: I-JEPA ViT-H is the largest and slowest option. If latency is too high on RTX 3060, may need to fall back to a smaller variant or DINOv2 ViT-L. Mitigation: benchmark early, design encoder interface as a swappable port.
- **Per-token diff resolution**: 16x16 is coarse. Each patch covers 14x14 pixels. For small product differences (e.g., serial number mismatch), this may not localize precisely enough. Mitigation: the heatmap is a guide for Gemma 4, not the final evidence — Gemma 4 can interpret the broader region.
- **Gemma 4 latency via Ollama**: 500ms-2s per explanation. This only fires on ~5% of requests (REJECT), but if Ollama is cold-starting or under load, it could timeout. Mitigation: set a 5-second timeout on the Ollama call, return the spatial diff without explanation on timeout.
- **VRAM pressure**: I-JEPA ViT-H FP16 (~3GB) + Gemma 4 (loaded separately by Ollama process, not in our VRAM) + OS overhead leaves ~7GB for batching. Comfortable for batch=1-8, tight for batch=16.

---
