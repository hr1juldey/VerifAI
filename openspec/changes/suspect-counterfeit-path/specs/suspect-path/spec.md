## ADDED Requirements

### Requirement: SUSPECT decision path
The system SHALL introduce a SUSPECT decision between MATCH and REJECT. SUSPECT SHALL trigger when global cosine similarity passes the per-product threshold but the 16x16 spatial diff map contains 2 or more contiguous patches exceeding the per-product regional threshold.

#### Scenario: Counterfeit with high global similarity
- **WHEN** global cosine similarity is 0.91 (above threshold) and 3 adjacent patches in the spatial diff map exceed the regional threshold
- **THEN** the system SHALL return decision=SUSPECT with the flagged patch coordinates and trigger the augmentation consistency test

#### Scenario: Genuine item with uniform spatial diff
- **WHEN** global cosine similarity is 0.89 (above threshold) and all 256 spatial diff patches are below the regional threshold
- **THEN** the system SHALL return decision=MATCH with no further processing

### Requirement: Augmentation consistency test
When SUSPECT is triggered, the system SHALL normalize the return image using CLAHE (Contrast Limited Adaptive Histogram Equalization), re-encode it through I-JEPA, and compare per-patch cosine deltas between raw and normalized encodings against the catalog embedding.

#### Scenario: Lighting artifact identified
- **WHEN** SUSPECT is triggered and the CLAHE-normalized encoding shows delta > 0.15 at flagged patches compared to raw encoding
- **THEN** the system SHALL resolve SUSPECT to MATCH with suspect_reason="LIGHTING_ARTIFACT"

#### Scenario: Content difference persists after normalization
- **WHEN** SUSPECT is triggered and the CLAHE-normalized encoding shows delta < 0.05 at flagged patches
- **THEN** the system SHALL escalate SUSPECT to REJECT with suspect_reason="CONTENT_DIFF" and trigger Gemma 4 explanation

#### Scenario: Ambiguous delta between thresholds
- **WHEN** SUSPECT is triggered and the CLAHE delta is between 0.05 and 0.15
- **THEN** the system SHALL retain decision=SUSPECT and trigger Gemma 4 for multimodal judgment

### Requirement: Per-product self-similarity baseline
At catalog ingestion, the system SHALL encode 5 augmented variants of the catalog image (random brightness/contrast, Gaussian blur, random shadow overlay, color temperature shift, small rotation) and compute per-product statistics: mean, std, min of their cosine similarities against the original catalog embedding.

#### Scenario: Baseline computed at ingestion
- **WHEN** a new product image is ingested via POST /catalog
- **THEN** the system SHALL encode 5 augmented variants, compute baseline {mean, std, min}, derive product_threshold = mean - 2*std and regional_threshold = min - 0.05, and store alongside the catalog embedding

#### Scenario: Low-variation product gets tight threshold
- **WHEN** a cotton t-shirt with consistent appearance is ingested and all 5 augmented variants score > 0.90 cosine similarity
- **THEN** the product_threshold SHALL be approximately 0.82 (tight, catches subtle counterfeits)

#### Scenario: High-variation product gets relaxed threshold
- **WHEN** a hand-embroidered kurta with natural variation is ingested and augmented variants score between 0.75-0.88
- **THEN** the product_threshold SHALL be approximately 0.68 (relaxed, avoids false SUSPECT)
