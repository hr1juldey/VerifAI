## ADDED Requirements

### Requirement: Store catalog embeddings by product ID

The cache must accept a product_id string and a global embedding tensor, storing them in memory for O(1) lookup.

#### Scenario: New product ingestion
- **WHEN** a product_id and embedding are stored
- **THEN** subsequent lookups by product_id return the embedding in <1ms

#### Scenario: Duplicate product_id ingestion
- **WHEN** an embedding is stored for an already-cached product_id
- **THEN** the existing embedding is replaced and the new one is stored

### Requirement: Retrieve catalog embedding by product ID

#### Scenario: Existing product lookup
- **WHEN** a product_id that exists in the cache is requested
- **THEN** the cached embedding tensor is returned

#### Scenario: Missing product lookup
- **WHEN** a product_id that does not exist in the cache is requested
- **THEN** None is returned (or a sentinel value)

### Requirement: Persist cache to disk

The cache must be serializable to a .pt file for persistence across server restarts.

#### Scenario: Save cache
- **WHEN** the cache is modified
- **THEN** it can be saved to a configurable file path as a PyTorch tensor dict

#### Scenario: Load cache at startup
- **WHEN** the server starts and a cache file exists
- **THEN** the cache is loaded from disk into memory

### Requirement: Report cache statistics

#### Scenario: Cache size query
- **WHEN** the cache is queried for statistics
- **THEN** it returns the number of cached products and estimated memory usage
