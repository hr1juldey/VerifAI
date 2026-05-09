## MODIFIED Requirements

### Requirement: DSPy signature with structured output
The DSPy ExplainRejection signature SHALL include a `verdict` output field in addition to the existing `explanation` field. The verdict SHALL be one of: LIGHTING_ARTIFACT, CONTENT_DIFF.

#### Scenario: Gemma identifies lighting as the cause
- **WHEN** the explainer receives a SUSPECT composite image where the red overlay covers a shadow region
- **THEN** the explainer SHALL return `{verdict: "LIGHTING_ARTIFACT", explanation: "Shadow on right side appears to be a lighting artifact; the product texture and pattern are consistent with the catalog image."}`

#### Scenario: Gemma identifies content difference
- **WHEN** the explainer receives a SUSPECT composite image where the red overlay covers a logo with different proportions
- **THEN** the explainer SHALL return `{verdict: "CONTENT_DIFF", explanation: "The swoosh logo at patch position (4,6) through (4,9) has visibly different proportions and curvature compared to the catalog."}`

#### Scenario: Gemma fallback on ambiguity
- **WHEN** the explainer cannot confidently determine lighting vs content
- **THEN** the explainer SHALL return `{verdict: "CONTENT_DIFF", explanation: "..."}` with explanation noting the uncertainty (conservative default to CONTENT_DIFF prevents false MATCH)
