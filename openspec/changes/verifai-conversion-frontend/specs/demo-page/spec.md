## ADDED Requirements

### Requirement: Demo page layout
The demo page SHALL display a two-panel layout with catalog image on the left and return image on the right, with a verification trigger between them.

#### Scenario: Demo page display
- **WHEN** user navigates to `/demo`
- **THEN** the system SHALL display a two-panel layout: left panel for catalog product image, right panel for return image, with a central "Verify" button

#### Scenario: Product selection
- **WHEN** the demo page loads
- **THEN** the system SHALL provide a product ID input and image upload areas for both catalog and return images

### Requirement: Live verification flow
The demo page SHALL submit images to `POST /verify` and render the real result.

#### Scenario: Manual verification
- **WHEN** user enters a product ID, uploads both images, and clicks "Verify"
- **THEN** the system SHALL submit to `/verify` as multipart form data and display the real result

#### Scenario: Product not in catalog
- **WHEN** the product ID has not been cataloged
- **THEN** the system SHALL first call `POST /catalog` with the catalog image, then call `POST /verify` with both images

#### Scenario: Network failure
- **WHEN** the API call fails
- **THEN** the system SHALL display "Connection to VerifAI backend lost" and allow retry

### Requirement: Animated heatmap bloom
The spatial diff heatmap SHALL animate with a bloom reveal effect, not display as a static image.

#### Scenario: Heatmap bloom animation
- **WHEN** the `spatial_diff_image` field is present in the verify response
- **THEN** the system SHALL render the heatmap with a radial gradient mask that blooms from center outward over 2.5 seconds

#### Scenario: Heatmap color ramp
- **WHEN** the heatmap renders
- **THEN** the system SHALL apply a color ramp: deep blue (#3b82f6, low diff) → yellow (#fbbf24, mid diff) → red (#ef4444, high diff)

#### Scenario: Hot spot pulsing glow
- **WHEN** the heatmap bloom completes
- **THEN** high-difference regions SHALL pulse with a glow effect at 0.5Hz for 3 seconds

#### Scenario: Heatmap fallback on mobile
- **WHEN** viewport width is below 768px
- **THEN** the system SHALL display the heatmap as a static image without animation

### Requirement: Typewriter AI explanation
The Gemma explanation SHALL reveal character-by-character with a typewriter effect.

#### Scenario: Typewriter reveal
- **WHEN** the `explanation` field is present in the verify response
- **THEN** the system SHALL display the explanation text character-by-character at approximately 60ms per character

#### Scenario: Explanation attribution
- **WHEN** the typewriter effect begins
- **THEN** the system SHALL display "Gemma 4 · VLM Explanation" as attribution above the explanation text

#### Scenario: No explanation available
- **WHEN** the `explanation` field is null or missing
- **THEN** the system SHALL display "Explanation unavailable" with no typewriter effect

### Requirement: Decision display with sound
The verification decision SHALL display with a color-coded badge and Web Audio API sound cue.

#### Scenario: MATCH decision
- **WHEN** the backend returns `decision: "MATCH"`
- **THEN** the system SHALL display a green (#4ade80) "MATCH" badge and play a soft ping sound via Web Audio API

#### Scenario: SUSPECT decision
- **WHEN** the backend returns `decision: "SUSPECT"`
- **THEN** the system SHALL display an amber (#fbbf24) "SUSPECT" badge and play a low alert tone via Web Audio API

#### Scenario: REJECT decision
- **WHEN** the backend returns `decision: "REJECT"`
- **THEN** the system SHALL display a red (#f87171) "REJECT" badge and play a low alert tone via Web Audio API

### Requirement: Analyzing state with hum
The demo page SHALL display an "Analyzing" state with a subtle audio hum during inference.

#### Scenario: Analyzing state display
- **WHEN** the verification request is in progress
- **THEN** the system SHALL display "Analyzing..." with a loading animation, elapsed time counter, and subtle hum via Web Audio API

#### Scenario: Hum stops on result
- **WHEN** the verification result is received
- **THEN** the hum SHALL stop immediately and the decision sound SHALL play

### Requirement: Sound toggle
The demo page SHALL provide a sound on/off toggle.

#### Scenario: Sound toggle
- **WHEN** user clicks the sound toggle
- **THEN** the system SHALL mute/unmute all audio cues (ping, alert, hum)

#### Scenario: Sound defaults on mobile
- **WHEN** the demo page loads on a viewport below 768px
- **THEN** sound SHALL default to muted

### Requirement: Director mode
The demo page SHALL include a hidden director mode for video recording, toggled by pressing the `D` key.

#### Scenario: Director mode activation
- **WHEN** user presses the `D` key
- **THEN** the system SHALL toggle director mode on, showing a "DIRECTOR" indicator in the corner

#### Scenario: Director mode deactivation
- **WHEN** user presses the `D` key again
- **THEN** the system SHALL toggle director mode off, hiding the "DIRECTOR" indicator

### Requirement: Director mode preset scenarios
Director mode SHALL provide 3 preset fraud scenarios triggered by keys `1`, `2`, `3`.

#### Scenario: Preset 1 — Genuine match
- **WHEN** user presses `1` in director mode
- **THEN** the system SHALL auto-fill catalog image (Saree_000) and return image (Saree_000), auto-catalog if needed, and trigger verification — expected result: MATCH (~0.97)

#### Scenario: Preset 2 — Same-category fraud
- **WHEN** user presses `2` in director mode
- **THEN** the system SHALL auto-fill catalog image (Saree_000) and return image (Saree_005), auto-catalog if needed, and trigger verification — expected result: SUSPECT (~0.58)

#### Scenario: Preset 3 — Cross-category swap
- **WHEN** user presses `3` in director mode
- **THEN** the system SHALL auto-fill catalog image (Sherwani_001) and return image (Saree_003), auto-catalog if needed, and trigger verification — expected result: REJECT (~0.12)

#### Scenario: Preset uses real API
- **WHEN** a director mode preset is triggered
- **THEN** the system SHALL call the real `/catalog` and `/verify` endpoints with real fixture images — not mock data

### Requirement: Director mode animation speed
Director mode SHALL allow adjustable animation speed for camera recording.

#### Scenario: Slow animation mode
- **WHEN** user presses `S` in director mode
- **THEN** the heatmap bloom and typewriter speeds SHALL be reduced to 50% (bloom: 5s, typewriter: ~120ms/char)

#### Scenario: Normal animation mode
- **WHEN** user presses `N` in director mode
- **THEN** the animation speeds SHALL return to default (bloom: 2.5s, typewriter: ~60ms/char)

### Requirement: Director mode replay
Director mode SHALL provide a replay button to re-trigger the last scenario cleanly.

#### Scenario: Replay button
- **WHEN** user clicks "Replay" in director mode
- **THEN** the system SHALL clear the current result and re-trigger the last preset scenario from the beginning

### Requirement: Demo page responsive
The demo page SHALL render correctly at all 5 breakpoints.

#### Scenario: Desktop recording layout (1920px)
- **WHEN** viewport is 1920px
- **THEN** the two-panel layout SHALL display side-by-side with maximum image size, heatmap at full resolution, and confidence scores in JetBrains Mono

#### Scenario: Mobile layout (375px)
- **WHEN** viewport is 375px
- **THEN** the panels SHALL stack vertically, heatmap SHALL render as static image, and director mode keyboard shortcuts SHALL be hidden
