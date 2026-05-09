## MODIFIED Requirements

### Requirement: Verify response schema
The POST /verify response SHALL include a three-way `decision` field: MATCH, SUSPECT, or REJECT. The response SHALL include an optional `suspect_reason` field (LIGHTING_ARTIFACT, CONTENT_DIFF, or null) and an optional `baseline_threshold` field showing the per-product threshold used.

#### Scenario: MATCH response
- **WHEN** a genuine return passes both global and regional checks
- **THEN** the system SHALL return `{decision: "MATCH", confidence: 0.91, suspect_reason: null, baseline_threshold: 0.82}`

#### Scenario: SUSPECT resolved to MATCH by augmentation consistency
- **WHEN** SUSPECT is triggered but CLAHE delta exceeds 0.15
- **THEN** the system SHALL return `{decision: "MATCH", confidence: 0.88, suspect_reason: "LIGHTING_ARTIFACT", baseline_threshold: 0.78}`

#### Scenario: SUSPECT escalated to REJECT
- **WHEN** SUSPECT is triggered and CLAHE delta is below 0.05
- **THEN** the system SHALL return `{decision: "REJECT", confidence: 0.73, suspect_reason: "CONTENT_DIFF", explanation: "...", spatial_diff_image: "..."}`

#### Scenario: Legacy product without baseline
- **WHEN** a product was ingested before baseline computation existed
- **THEN** the system SHALL fall back to the global VERIFICATION_THRESHOLD env var and omit `baseline_threshold` from the response

### Requirement: Verify latency targets
The system SHALL maintain the following latency targets: MATCH path under 40ms, SUSPECT path (augmentation consistency only, no Gemma) under 100ms, REJECT with Gemma explanation under 2s.

#### Scenario: MATCH latency
- **WHEN** a request resolves to MATCH (no SUSPECT, no REJECT)
- **THEN** the latency_ms field SHALL be under 40ms

#### Scenario: SUSPECT with augmentation consistency
- **WHEN** SUSPECT triggers and augmentation consistency test runs
- **THEN** the latency_ms field SHALL be under 100ms (one extra I-JEPA forward pass + CLAHE)
