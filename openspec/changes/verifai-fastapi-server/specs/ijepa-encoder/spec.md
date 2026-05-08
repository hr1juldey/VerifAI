## ADDED Requirements

### Requirement: Load I-JEPA model at startup in FP16

The server must load `facebook/ijepa_vith14_22k` via HuggingFace `AutoModel` during FastAPI lifespan startup. The model must be converted to FP16 and moved to CUDA. It must remain loaded for the process lifetime.

#### Scenario: Server starts with GPU available
- **WHEN** the FastAPI lifespan starts and CUDA is available
- **THEN** the I-JEPA ViT-H/14 model is loaded in FP16, moved to GPU, set to eval mode, and stored in app.state

#### Scenario: Server starts without GPU
- **WHEN** the FastAPI lifespan starts and CUDA is not available
- **THEN** the server starts with the model on CPU in FP32 and logs a warning about degraded performance

### Requirement: Extract global embedding from an image

Given a PIL Image or tensor, the encoder must return a global embedding vector via mean pooling on `last_hidden_state`.

#### Scenario: Single image embedding extraction
- **WHEN** an image is passed through the encoder
- **THEN** it returns a tensor of shape [1024] (mean-pooled from [1, 256, 1024])

### Requirement: Extract per-token embeddings from an image

The encoder must also return the raw `last_hidden_state` for spatial diff computation.

#### Scenario: Per-token embedding extraction
- **WHEN** an image is passed through the encoder with `return_tokens=True`
- **THEN** it returns a tensor of shape [256, 1024] (the raw token embeddings before pooling)

### Requirement: Batch inference for image pairs

The encoder must accept a pair of images and process them in a single forward pass (batch=2) to minimize latency.

#### Scenario: Catalog and return image pair
- **WHEN** two images are passed as a batch
- **THEN** both embeddings are computed in a single GPU kernel launch (~15-25ms on RTX 3060)
