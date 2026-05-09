## MODIFIED Requirements

### Requirement: Per-product baseline storage
The embedding store SHALL store a dict per product containing `embedding` (tensor) and `baseline` (dict with mean, std, min, threshold, regional_threshold, delta_threshold). The .pt file format SHALL be backward compatible: entries without a baseline dict SHALL fall back to global defaults.

#### Scenario: Store product with baseline
- **WHEN** a product is ingested with baseline statistics computed
- **THEN** the store SHALL save `{embedding: tensor, baseline: {mean: 0.88, std: 0.04, min: 0.82, threshold: 0.80, regional_threshold: 0.77, delta_threshold: 0.15}}`

#### Scenario: Load legacy .pt file without baselines
- **WHEN** the store loads a .pt file containing `{product_id: tensor}` format (old format)
- **THEN** the store SHALL convert each entry to `{embedding: tensor, baseline: null}` and lookups SHALL return the global default threshold

#### Scenario: Retrieve baseline for verify
- **WHEN** get_baseline("SKU-001") is called for a product with stored baseline
- **THEN** the store SHALL return the baseline dict; if no baseline exists, return None
