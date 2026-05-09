## ADDED Requirements

### Requirement: Calibration feedback endpoint
The system SHALL expose POST /calibrate accepting `{product_id: str, category: str, decision: str, human_label: str, cosine_sim: float}`. The system SHALL append each submission as a JSONL line to a configurable file path (env: CALIBRATION_PATH, default: data/calibration.jsonl).

#### Scenario: Human reviews a SUSPECT decision
- **WHEN** a warehouse manager reviews a SUSPECT result and submits `{product_id: "SKU-001", category: "saree", decision: "SUSPECT", human_label: "genuine", cosine_sim: 0.71}`
- **THEN** the system SHALL append the entry to data/calibration.jsonl and return 200 with `{status: "recorded"}`

#### Scenario: Missing required fields
- **WHEN** POST /calibrate is called without product_id or human_label
- **THEN** the system SHALL return 422 with a validation error message

### Requirement: Per-category error rate computation
The system SHALL expose GET /calibration/stats returning per-category Type 1 rate (false SUSPECT/REJECT on genuine items) and Type 2 rate (false MATCH on counterfeit items) computed from the calibration JSONL.

#### Scenario: Category with mixed results
- **WHEN** GET /calibration/stats is called and calibration.jsonl contains 20 saree entries where 2 were false SUSPECT and 1 was false MATCH
- **THEN** the system SHALL return `{saree: {type1_rate: 0.10, type2_rate: 0.05, total: 20}}`

#### Scenario: No calibration data
- **WHEN** GET /calibration/stats is called and calibration.jsonl does not exist
- **THEN** the system SHALL return `{status: "no_data"}`
