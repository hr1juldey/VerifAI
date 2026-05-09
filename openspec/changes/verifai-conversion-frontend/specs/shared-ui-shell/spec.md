## ADDED Requirements

### Requirement: Astro app shell
The system SHALL use Astro 5 as the app shell with React islands for interactive components.

#### Scenario: Static page rendering
- **WHEN** the user navigates to a page with no interactive components
- **THEN** the system SHALL serve pure static HTML with zero client-side JavaScript

#### Scenario: React island hydration
- **WHEN** a page includes an interactive component (heatmap, demo, preview)
- **THEN** only that component SHALL hydrate as a React island — all other content remains static

### Requirement: Warehouse Dark design system
The system SHALL apply the "Warehouse Dark" design tokens globally.

#### Scenario: Color tokens
- **WHEN** any page renders
- **THEN** the system SHALL use the following CSS custom properties: `--bg: #08080d`, `--surface: #12121a`, `--border: #1e1e2e`, `--accent: #818cf8`, `--success: #4ade80`, `--danger: #f87171`, `--warning: #fbbf24`, `--text: #f1f5f9`, `--muted: #94a3b8`

#### Scenario: Typography stack
- **WHEN** any page renders
- **THEN** display text SHALL use Space Grotesk (48-72px, weight 700, letter-spacing -0.02em), body text SHALL use Inter (16px, weight 400/500, line-height 1.6), and data/scores SHALL use JetBrains Mono

### Requirement: Navigation
The system SHALL provide navigation between pages.

#### Scenario: Navigation links
- **WHEN** the application loads
- **THEN** the system SHALL display navigation links for "Demo" and "Dashboard" (landing page is accessed via site logo/home link)

#### Scenario: Active route indication
- **WHEN** user is on the `/demo` page
- **THEN** the "Demo" navigation link SHALL be visually highlighted with the accent color

### Requirement: 5-breakpoint responsive system
The system SHALL support all 5 responsive breakpoints with Tailwind CSS.

#### Scenario: Mobile (375px)
- **WHEN** viewport width is 375px
- **THEN** the layout SHALL be single-column, navigation SHALL collapse to a hamburger menu, and font sizes SHALL scale down (display: 28px)

#### Scenario: Tablet (768px)
- **WHEN** viewport width is 768px
- **THEN** the layout SHALL be single-column with wider content areas, heatmap animations SHALL fall back to static images, and sound SHALL default to muted

#### Scenario: Desktop (1024px)
- **WHEN** viewport width is 1024px
- **THEN** the layout SHALL support side-by-side panels and full animation support

#### Scenario: Large desktop (1440px)
- **WHEN** viewport width is 1440px
- **THEN** the layout SHALL use a max-width container with comfortable spacing

#### Scenario: Full HD recording (1920px)
- **WHEN** viewport width is 1920px
- **THEN** the layout SHALL fill the viewport with maximum image size, full-resolution heatmap, and display text at 72px

### Requirement: Image upload component (React island)
The system SHALL provide a reusable image upload React island component.

#### Scenario: Drag and drop support
- **WHEN** user drags an image file over the upload area
- **THEN** the component SHALL display a visual drop zone indicator with accent color border

#### Scenario: File picker fallback
- **WHEN** user clicks the upload area
- **THEN** a file picker dialog SHALL open filtered to image files (.png, .jpg, .jpeg)

#### Scenario: Image preview
- **WHEN** an image is selected
- **THEN** the component SHALL render a thumbnail preview of the image

#### Scenario: Clear selected image
- **WHEN** user clicks the clear button on the preview
- **THEN** the component SHALL remove the preview and reset to the empty upload state

#### Scenario: File validation
- **WHEN** user selects a non-image file or a file exceeding 10MB
- **THEN** the component SHALL display an error and reject the file

### Requirement: Status badge component (React island)
The system SHALL provide a reusable decision badge React island component.

#### Scenario: MATCH badge
- **WHEN** rendered with "MATCH" variant
- **THEN** the badge SHALL display #4ade80 background with "MATCH" text

#### Scenario: SUSPECT badge
- **WHEN** rendered with "SUSPECT" variant
- **THEN** the badge SHALL display #fbbf24 background with "SUSPECT" text

#### Scenario: REJECT badge
- **WHEN** rendered with "REJECT" variant
- **THEN** the badge SHALL display #f87171 background with "REJECT" text

### Requirement: Error notification system
The system SHALL display error notifications for API failures.

#### Scenario: Error toast display
- **WHEN** an API call fails
- **THEN** the system SHALL display a toast notification with the error message using the danger color, auto-dismissing after 5 seconds
