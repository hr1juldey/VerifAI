## ADDED Requirements

### Requirement: Download fixture images from Indo Fashion dataset
The system SHALL provide a script `scripts/download_fixtures.py` that downloads the `validmodel/indo-fashion-dataset` Kaggle dataset via kagglehub, selects 40 images (10 each from saree, kurta, sherwani, lehenga categories), copies them to `tests/fixtures/images/`, and generates a `tests/fixtures/manifest.json` with per-image metadata (image_path, category, brand, product_title, class_label).

#### Scenario: Fresh download with no existing fixtures
- **WHEN** `scripts/download_fixtures.py` is run and `tests/fixtures/images/` does not exist
- **THEN** the script SHALL download the dataset via kagglehub, create `tests/fixtures/images/`, copy 10 images per category (40 total), and write `tests/fixtures/manifest.json`

#### Scenario: Fixtures already exist
- **WHEN** `scripts/download_fixtures.py` is run and `tests/fixtures/manifest.json` already exists with 40 entries
- **THEN** the script SHALL skip downloading and print "Fixtures already exist"

### Requirement: GPU-gated integration test marker
All tests that require the I-JEPA encoder GPU SHALL be marked with `@pytest.mark.gpu`. The conftest.py SHALL provide a `real_encoder` fixture that loads the actual I-JEPA model. Tests without the marker SHALL NOT require GPU.

#### Scenario: Run GPU tests only
- **WHEN** `pytest -m gpu` is run on a machine with CUDA
- **THEN** all tests marked `@pytest.mark.gpu` SHALL execute with the real I-JEPA encoder

#### Scenario: Skip GPU tests
- **WHEN** `pytest -m "not gpu"` is run
- **THEN** all GPU-dependent tests SHALL be skipped and unit tests SHALL pass

### Requirement: Baseline computation with real images
The test suite SHALL verify that `compute_baseline` produces valid `ProductBaseline` statistics when given real product images encoded through the I-JEPA encoder. Baseline mean SHALL be between 0.5 and 1.0 for same-product augmented variants.

#### Scenario: Saree baseline computation
- **WHEN** `compute_baseline` is called with a real saree image from fixtures
- **THEN** the returned `ProductBaseline` SHALL have mean >= 0.5, std >= 0.01, threshold derived as mean - 2*std, and all fields populated

#### Scenario: Baseline varies by category
- **WHEN** baselines are computed for a kurta image and a sherwani image
- **THEN** the thresholds MAY differ, reflecting per-product variation

### Requirement: SUSPECT path test with real spatial diffs
The test suite SHALL verify the SUSPECT decision path by ingesting a real catalog image, submitting a different image of the same category as a return, and confirming the three-way decision logic (MATCH / SUSPECT / REJECT) produces a valid result.

#### Scenario: Same product returns MATCH
- **WHEN** a catalog saree image is ingested and the same image is submitted for verification
- **THEN** the result SHALL have decision="MATCH" and confidence close to 1.0

#### Scenario: Different product triggers REJECT or SUSPECT
- **WHEN** a catalog kurta image is ingested and a different kurta from a different brand is submitted
- **THEN** the result SHALL have decision in ("SUSPECT", "REJECT") with suspect_reason populated if SUSPECT

### Requirement: CLAHE augmentation consistency with real images
The test suite SHALL verify that `normalize_clahe` produces a valid image that can be re-encoded by the I-JEPA encoder, and that the augmentation consistency test runs end-to-end on real data.

#### Scenario: CLAHE on dim warehouse photo
- **WHEN** a real product image with uneven lighting is passed through `normalize_clahe`
- **THEN** the output SHALL be a valid numpy array with the same shape as input, and re-encoding SHALL produce a valid 256x1024 token tensor

### Requirement: Calibration endpoint integration test
The test suite SHALL verify the POST /calibrate and GET /calibration/stats endpoints with real data written to a temporary JSONL file.

#### Scenario: Full calibration round trip
- **WHEN** a calibration entry is POSTed for a saree product and then GET /calibration/stats is called
- **THEN** the stats SHALL include the saree category with correct type1_rate and type2_rate
