## Why

VerifAI has a working backend (I-JEPA encoder, spatial diff, Gemma explanation) but zero visual presence. For a fellowship evaluation, the product must be experienced in a 3-minute demo video followed by a live URL visit. Every pixel must serve the camera first, the evaluator's browser second. This frontend is a **conversion instrument**, not an operator dashboard — designed to make evaluators say "I want this."

## What Changes

- Build a static-first web frontend using Astro 5 with React islands for interactive components
- Create a landing page (`/`) with hero section, looping verification preview animation, stats bar, pain section, and CTA pair
- Create a demo page (`/demo`) as the #1 priority — live verification with animated heatmap bloom, typewriter AI explanation, sound design, and hidden director mode for clean video recording
- Implement "Warehouse Dark" design system optimized for camera recording (near-black background makes colors pop on compressed video)
- Support all 5 responsive breakpoints: 375px (mobile sharing), 768px (tablet), 1024px (laptop), 1440px (desktop), 1920px (demo recording)
- Waitlist/CTA capture mechanism to be decided later (placeholder for now)
- Defer dashboard (`/dashboard`) and ROI calculator (`/roi`) pages to a later change
- No backend changes — consume existing `/catalog`, `/verify`, `/health` endpoints

## Capabilities

### New Capabilities
- `landing-page`: Hero section with headline/subheadline, looping verification preview, stats bar, pain section, tech cred, CTA pair with waitlist
- `demo-page`: Live verification flow, animated heatmap bloom, typewriter explanation, sound design, hidden director mode with 3 preset scenarios
- `system-dashboard-ui`: System health status and calibration stats (DEFERRED — spec written, implementation in later change)
- `shared-ui-shell`: Astro app shell, Warehouse Dark design tokens, navigation, responsive breakpoints, shared React island components

### Modified Capabilities
(none — no existing specs)

## Impact

- **New code**: `frontend/` directory with Astro 5 project, React islands for interactive components
- **API layer**: No backend changes — existing endpoints consumed as-is
- **Dependencies**: Astro 5, React (islands only), Tailwind CSS, Web Audio API (native)
- **Assets**: Fixture images from `data/fixtures/{category}/{category}_{000-009}.jpg` for director mode presets
- **External**: Tally.so or Google Form embed for waitlist capture
