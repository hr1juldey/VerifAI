## ADDED Requirements

### Requirement: Hero section
The landing page SHALL display a full-viewport hero section with headline, subheadline, and CTA pair.

#### Scenario: Hero section display
- **WHEN** user navigates to `/`
- **THEN** the system SHALL display a hero section occupying the full viewport with headline "Catch return fraud. In 1.8 seconds.", subheadline "JEPA-powered visual verification for Indian e-commerce", and two CTA buttons

#### Scenario: Primary CTA
- **WHEN** user clicks the primary CTA "Try it live"
- **THEN** the system SHALL navigate to `/demo`

#### Scenario: Secondary CTA
- **WHEN** user clicks the secondary CTA "Get early access"
- **THEN** the system SHALL open the waitlist form (Tally.so embed or inline form)

### Requirement: Live verification preview
The hero section SHALL include a looping animation showing a SUSPECT verification result.

#### Scenario: Preview animation loop
- **WHEN** the landing page loads
- **THEN** the system SHALL display an animated verification preview that cycles through a SUSPECT result every 8 seconds, showing image upload → analyzing state → SUSPECT decision → heatmap reveal

#### Scenario: Preview is a React island
- **WHEN** the verification preview component renders
- **THEN** only the preview component SHALL hydrate as a React island — the rest of the landing page SHALL be static HTML

### Requirement: Stats bar
The landing page SHALL display a stats bar below the hero section.

#### Scenario: Stats bar content
- **WHEN** the landing page renders
- **THEN** the system SHALL display a stats bar with: "10 images to deploy", "1.8s latency", "98.6% accuracy"

### Requirement: Pain section
The landing page SHALL display a section quantifying the return fraud problem.

#### Scenario: Pain section content
- **WHEN** the landing page renders below the stats bar
- **THEN** the system SHALL display "₹1,000+ Crore lost to return fraud annually" with supporting context about return rates and costs

### Requirement: Tech credibility section
The landing page SHALL display the underlying technology stack.

#### Scenario: Tech cred display
- **WHEN** the tech cred section renders
- **THEN** the system SHALL display "Built with I-JEPA · ViT-H/14 · 632M parameters" and a brief description of why JEPA beats traditional CV

### Requirement: Tertiary CTA
The landing page SHALL provide a "Talk to founder" call-to-action.

#### Scenario: Talk to founder CTA
- **WHEN** user clicks "Talk to founder"
- **THEN** the system SHALL open a Calendly link or WhatsApp chat

### Requirement: Waitlist placeholder
The landing page SHALL display a "Get early access" CTA that shows a coming-soon state (actual form TBD).

#### Scenario: Waitlist CTA
- **WHEN** user clicks "Get early access"
- **THEN** the system SHALL show a "Coming soon" message or navigate to a placeholder route (actual waitlist integration deferred)

### Requirement: Responsive landing page
The landing page SHALL render correctly at all 5 breakpoints.

#### Scenario: Mobile layout (375px)
- **WHEN** viewport width is 375px
- **THEN** the hero section SHALL stack vertically, headline SHALL scale to 28px, CTAs SHALL be full-width, and the preview animation SHALL be hidden or replaced with a static image

#### Scenario: Full HD layout (1920px)
- **WHEN** viewport width is 1920px
- **THEN** the hero section SHALL use max-width container, headline SHALL render at 72px, and the preview animation SHALL be prominently displayed
