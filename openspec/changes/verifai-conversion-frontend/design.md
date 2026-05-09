## Context

VerifAI is a JEPA-powered visual verification platform for Indian e-commerce return fraud detection. The backend (FastAPI, I-JEPA ViT-H/14, Gemma 4 VLM) is functional. This frontend exists for one purpose: **convert a 3-minute demo video viewer into a believer**.

The evaluator watches a recorded demo, then visits the live URL. The frontend must look stunning on camera (1920px recording) and work flawlessly on mobile (375px social sharing). It is NOT a daily-use operator dashboard — it is a pitch instrument.

Fixture images are available at `data/fixtures/{category}/{category}_{000-009}.jpg` with 4 categories (saree, kurta, lehenga, sherwani), 10 images each.

## Goals / Non-Goals

**Goals:**
- Convert fellowship evaluators via a compelling demo video + live URL experience
- Demonstrate I-JEPA verification in real-time with animated heatmap and AI explanation
- Provide director mode for clean, repeatable video recording scenarios
- Look cinematic on camera (Warehouse Dark design system)
- Work across all 5 breakpoints (375, 768, 1024, 1440, 1920px)
- Capture waitlist signups from interested evaluators

**Non-Goals:**
- Authentication or multi-user sessions
- Real-time WebSocket updates (verification is request-response)
- Dashboard or ROI calculator (deferred to later change)
- Offline mode or PWA
- Custom backend for waitlist (use Tally.so/Google Form)
- Mobile-native app

## Decisions

### 1. Astro 5 with React Islands
**Choice**: Astro 5 as the framework, React only for interactive islands.
**Rationale**: Static-first means zero JS shipped for landing page content. React loads only for the interactive demo, heatmap, and upload components. This gives instant page loads for the landing page (critical for first impression) while keeping rich interactivity where needed.
**Alternatives considered**: Next.js (overkill, ships too much JS for a static landing page), Vite SPA (no static-first optimization, entire app loads upfront), plain HTML (can't do heatmap animation or director mode).

### 2. "Warehouse Dark" Design System
**Choice**: Near-black background (`#08080d`) with indigo accent (`#818cf8`), bright status colors.
**Rationale**: Dark backgrounds make colors pop dramatically on camera. Compressed video (YouTube, Loom) washes out light colors but dark backgrounds keep contrast. The indigo accent is visible even on heavily compressed video.
**Tokens**:
```
--bg: #08080d; --surface: #12121a; --border: #1e1e2e;
--accent: #818cf8; --success: #4ade80; --danger: #f87171; --warning: #fbbf24;
--text: #f1f5f9; --muted: #94a3b8;
Display: Space Grotesk 48-72px/700/-0.02em tracking;
Body: Inter 16px/400-500/1.6; Data: JetBrains Mono for scores/API values
```

### 3. Heatmap Bloom Animation (React Canvas Island)
**Choice**: Canvas-based radial gradient bloom animation with CSS pulsing glow overlay.
**Rationale**: The spatial diff heatmap is the hero shot — the single most differentiated visual. No competitor shows WHERE the AI sees differences. The bloom animation (center outward over 2.5s with color ramp blue→yellow→red) creates a cinematic reveal moment. Pulsing glow on hot spots (0.5Hz for 3s) draws the eye.
**Alternatives considered**: Static image (boring, no drama), SVG animation (can't handle pixel-level heatmap data efficiently), WebGL (overkill for a single overlay).

### 4. Director Mode via Keyboard Shortcuts
**Choice**: Hidden mode toggled by pressing `D`, with presets on `1`/`2`/`3`.
**Rationale**: Video recording needs repeatable, clean scenarios. Director mode auto-fills fixture images for 3 preset fraud scenarios, hits the real API, and renders real results. Adjustable animation speed lets the presenter slow down for camera clarity. "Replay" button re-triggers cleanly.
**Presets**: `1`=Genuine match (Saree_000→Saree_000, ~0.97), `2`=Same-category fraud (Saree_000→Saree_005, ~0.58 SUSPECT), `3`=Cross-category swap (Sherwani_001→Saree_003, ~0.12 REJECT).

### 5. Typewriter Effect for AI Explanation
**Choice**: Character-by-character reveal at ~60ms per character.
**Rationale**: Real inference takes 5-15 seconds. The typewriter effect builds tension and makes the wait feel intentional rather than laggy. Attribution line "Gemma 4 · VLM Explanation" establishes technical credibility.

### 6. Web Audio API Sound Design
**Choice**: Native Web Audio API oscillators for 3 sound cues + analyzing hum.
**Rationale**: No external audio files needed. Soft ping (MATCH), low alert (SUSPECT), subtle hum (analyzing). Toggle on/off for silent recording. Creates emotional texture — trust for matches, tension for fraud.

### 7. Landing Page as Static Astro Page
**Choice**: The `/` route is a pure Astro page with zero client-side JS except the looping verification preview (React island).
**Rationale**: Landing page must load instantly for first impression. Static HTML with CSS animations for the preview loop. Only the preview component hydrates as a React island.

### 8. Waitlist via Tally.so Embed
**Choice**: Embed Tally.so popup or inline form for waitlist capture.
**Rationale**: Zero backend work. Tally provides name, email, company type fields out of the box. Can be replaced later with a custom form if volume justifies it.

### 9. Monorepo Structure — `frontend/` at Project Root
**Choice**: `frontend/` directory, Astro build outputs to `frontend/dist/`.
**Rationale**: Clean separation from Python backend. FastAPI mounts `frontend/dist/` via `StaticFiles` in production. During dev, Astro dev server (port 4321) proxies API calls to FastAPI (port 8000).

### 10. All 5 Responsive Breakpoints
**Choice**: Tailwind breakpoints configured for 375, 768, 1024, 1440, 1920px.
**Rationale**: Demo recording at 1920px, landing page shared on mobile at 375px. Every breakpoint is a real use case: mobile social sharing → evaluator phone visit → laptop review → desktop deep-dive → camera recording.

## Risks / Trade-offs

- **[Heatmap animation performance on mobile]** → Fallback to static image on viewports < 768px. Canvas animation only on desktop/tablet.
- **[Director mode preset accuracy]** → Presets call real API with real fixture images. Results vary slightly per run (embedding quantization). Acceptable — shows system is live, not scripted.
- **[No auth]** → Acceptable for demo/fellowship context. Backend is local-only behind firewall.
- **[Audio autoplay restrictions]** → Sound initializes on first user interaction (click). Director mode `D` key press counts as interaction. Audio toggle defaults to off on mobile.
- **[Astro + React island bundle size]** → React only loads on pages with islands (demo, landing preview). Static pages ship zero JS. Target < 50KB JS on demo page, < 5KB on landing page.
