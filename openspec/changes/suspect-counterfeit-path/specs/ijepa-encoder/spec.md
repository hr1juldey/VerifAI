## MODIFIED Requirements

### Requirement: Batch encode with augmentations
The I-JEPA encoder SHALL support encoding a list of augmented image variants in a single batch call, returning one embedding per variant. This SHALL be used at catalog ingestion time to compute the self-similarity baseline.

#### Scenario: Encode 5 augmented variants
- **WHEN** encode_batch is called with a list of 5 augmented images
- **THEN** the encoder SHALL return a tensor of shape [5, 1024] containing one pooled embedding per variant

#### Scenario: Single image encode unchanged
- **WHEN** encode_image is called with a single image (no return_tokens flag)
- **THEN** behavior SHALL remain identical to the current implementation (backward compatible)

### Requirement: CLAHE preprocessing utility
The encoder module SHALL expose a function to apply CLAHE normalization to an image, returning the normalized image suitable for re-encoding.

#### Scenario: CLAHE normalizes dim warehouse photo
- **WHEN** a return image with uneven lighting (bright left, dark right) is passed to the CLAHE function
- **THEN** the output image SHALL have locally normalized contrast while preserving texture and pattern details
