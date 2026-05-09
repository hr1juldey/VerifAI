## MODIFIED Requirements

### Requirement: Regional threshold parameter
The spatial diff compute_diff function SHALL accept an optional regional_threshold parameter. When provided, it SHALL flag patches where the diff score exceeds this threshold. The function SHALL return the flagged patch count and contiguous region count in addition to the existing SpatialDiffMap.

#### Scenario: Regional threshold catches localized counterfeit
- **WHEN** compute_diff is called with regional_threshold=0.25 and the diff map has a 3-patch contiguous region at (4,6)-(4,8) with values above 0.25
- **THEN** the result SHALL include flagged_count=3 and contiguous_regions=1

#### Scenario: No patches exceed regional threshold
- **WHEN** compute_diff is called with regional_threshold=0.30 and all 256 patches are below 0.30
- **THEN** the result SHALL include flagged_count=0 and contiguous_regions=0

### Requirement: Per-patch cosine delta computation
The spatial diff module SHALL expose a function to compute per-patch cosine delta between raw and normalized token sets, given two sets of tokens from the same image (raw and CLAHE-normalized) and catalog tokens as reference.

#### Scenario: Large delta at shadow patch
- **WHEN** per_patch_delta is computed for a return image with shadow on patch (6,3), and the CLAHE-normalized encoding at that patch has cosine 0.88 vs catalog while raw has 0.55
- **THEN** the delta at patch (6,3) SHALL be 0.33
