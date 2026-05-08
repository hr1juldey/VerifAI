## ADDED Requirements

### Requirement: POST /verify endpoint

Accept a return image and product_id, run the full verification pipeline, and return a MATCH or REJECT decision with optional explanation.

#### Scenario: Matching product return
- **WHEN** POST /verify is called with a return image that matches the catalog embedding for the given product_id (cosine similarity >= threshold, default 0.7)
- **THEN** response status is 200 with `decision: "MATCH"`, `confidence: <float>`, `latency_ms: <int>`, and no explanation

#### Scenario: Mismatched product return
- **WHEN** POST /verify is called with a return image that does NOT match (cosine similarity < threshold)
- **THEN** response status is 200 with `decision: "REJECT"`, `confidence: <float>`, `latency_ms: <int>`, `spatial_diff_image: <base64>`, and `explanation: <string>` (from Gemma 4)

#### Scenario: Unknown product_id
- **WHEN** POST /verify is called with a product_id not in the embedding cache
- **THEN** response status is 404 with an error message indicating the product is not registered

### Requirement: POST /catalog endpoint

Accept a product image and product_id, compute the I-JEPA embedding, and store it in the cache.

#### Scenario: New product cataloged
- **WHEN** POST /catalog is called with a product image and product_id
- **THEN** the embedding is computed, stored in cache, and response is 201 with product_id and embedding dimensions

#### Scenario: Product re-cataloged
- **WHEN** POST /catalog is called with an existing product_id
- **THEN** the existing embedding is replaced with the new one

### Requirement: GET /health endpoint

#### Scenario: Health check
- **WHEN** GET /health is called
- **THEN** response includes GPU status, model loaded status, cache size, and Ollama connectivity

### Requirement: Async GPU concurrency

The server must handle concurrent verification requests without blocking, using a semaphore to control GPU access.

#### Scenario: Multiple concurrent requests
- **WHEN** 2+ verify requests arrive simultaneously
- **THEN** they are interleaved on the GPU via semaphore(2), each receiving independent results without blocking the event loop

### Requirement: Configurable match threshold

The cosine similarity threshold for MATCH/REJECT must be configurable via environment variable (default 0.7).

#### Scenario: Custom threshold
- **WHEN** env var VERIFICATION_THRESHOLD is set to 0.85
- **THEN** only embeddings with cosine similarity >= 0.85 result in MATCH
