## ADDED Requirements

### Requirement: Compute per-token cosine similarity map

Given two per-token embedding tensors of shape [256, 1024], compute a cosine similarity score for each of the 256 token pairs, producing a [256] vector.

#### Scenario: Identical images
- **WHEN** two identical images are compared
- **THEN** all 256 per-token similarities are ~1.0

#### Scenario: Completely different images
- **WHEN** two semantically different images are compared
- **THEN** per-token similarities are low (typically 0.2-0.4)

### Requirement: Reshape similarity vector to spatial heatmap

The [256] similarity vector must be reshaped to [16, 16] and then upscaled to match the original image dimensions using bilinear interpolation.

#### Scenario: Heatmap generation
- **WHEN** a [256] similarity vector is provided
- **THEN** a 2D numpy array matching the input image dimensions is produced with values in [0, 1]

### Requirement: Overlay heatmap on original image

The heatmap must be rendered as a red/orange colormap (low similarity = red) and blended onto the original image using OpenCV with a configurable alpha.

#### Scenario: Overlay rendering
- **WHEN** a return image and spatial diff map are provided
- **THEN** an annotated image is produced with red-highlighted regions where similarity is below a configurable threshold (default 0.5)

### Requirement: Side-by-side composite for Gemma input

The catalog image and annotated return image must be concatenated horizontally into a single composite image suitable for Gemma 4 multimodal input.

#### Scenario: Composite generation
- **WHEN** a catalog image and annotated return image are provided
- **THEN** a single side-by-side image is produced with catalog on the left and annotated return on the right
