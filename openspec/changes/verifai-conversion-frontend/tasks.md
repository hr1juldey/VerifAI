## 1. Project Setup & Design System

- [x] 1.1 Initialize Astro 5 project in `frontend/` with TypeScript
- [x] 1.2 Install React integration (`@astrojs/react`) and configure React islands
- [x] 1.3 Install and configure Tailwind CSS with custom Warehouse Dark design tokens (--bg, --surface, --border, --accent, --success, --danger, --warning, --text, --muted)
- [x] 1.4 Configure Tailwind custom breakpoints: sm=375, md=768, lg=1024, xl=1440, 2xl=1920
- [x] 1.5 Set up font loading: Space Grotesk (display), Inter (body), JetBrains Mono (data)
- [x] 1.6 Configure Astro dev server proxy to forward `/api/*` to FastAPI (localhost:8000)
- [x] 1.7 Create TypeScript API client module with typed interfaces for CatalogResponse, VerifyResponse, HealthResponse, ErrorResponse

## 2. Shared Components (React Islands)

- [x] 2.1 Build ImageUpload React island component with drag-and-drop zone, file picker, thumbnail preview, clear button, and file validation (image types, 10MB limit)
- [x] 2.2 Build StatusBadge React island component with MATCH (#4ade80), SUSPECT (#fbbf24), REJECT (#f87171) variants
- [x] 2.3 Build ErrorToast React island component with auto-dismiss after 5 seconds
- [x] 2.4 Build SoundEngine module using Web Audio API: soft ping (MATCH), low alert (SUSPECT/REJECT), analyzing hum, mute toggle

## 3. App Shell & Navigation

- [x] 3.1 Create Astro base layout with Warehouse Dark design system, global styles, font imports
- [x] 3.2 Build navigation component with links: Demo, Dashboard (landing via logo/home)
- [x] 3.3 Implement Astro page routing: `/` (landing), `/demo`, `/dashboard`
- [x] 3.4 Add responsive navigation: sidebar on desktop (1024px+), hamburger menu on mobile/tablet

## 4. Landing Page (`/`)

- [x] 4.1 Build hero section: headline ("Catch return fraud. In 1.8 seconds."), subheadline, CTA pair (primary: "Try it live" → /demo, secondary: "Get early access" → waitlist)
- [x] 4.2 Build looping verification preview React island: cycles SUSPECT result every 8 seconds (upload → analyzing → SUSPECT → heatmap reveal)
- [x] 4.3 Build stats bar: "10 images to deploy · 1.8s latency · 98.6% accuracy"
- [x] 4.4 Build pain section: "₹1,000+ Crore lost to return fraud annually" with supporting context
- [x] 4.5 Build tech cred section: "Built with I-JEPA · ViT-H/14 · 632M parameters"
- [x] 4.6 Add "Get early access" CTA button with placeholder coming-soon state (waitlist provider TBD)
- [x] 4.7 Add "Talk to founder" CTA (Calendly or WhatsApp link)
- [x] 4.8 Implement responsive hero: 72px headline at 1920px, 28px at 375px, stacked CTAs on mobile

## 5. Demo Page — Core Verification (`/demo`)

- [x] 5.1 Build two-panel demo layout: catalog image (left), return image (right), verify button (center)
- [x] 5.2 Add product ID input and ImageUpload islands for both catalog and return images
- [x] 5.3 Implement auto-cataloging: if product not found, call POST /catalog first, then POST /verify
- [x] 5.4 Build verification result display: decision badge, confidence score (JetBrains Mono), latency, baseline threshold
- [x] 5.5 Build "Analyzing..." state with elapsed time counter and analyzing hum sound
- [x] 5.6 Add sound toggle button (defaults muted on mobile)
- [x] 5.7 Handle error states: backend unreachable, product not found, network failure

## 6. Demo Page — Heatmap Bloom Animation

- [x] 6.1 Build HeatmapBloom React island: Canvas-based heatmap rendering with base64 spatial_diff_image data
- [x] 6.2 Implement radial gradient mask bloom animation: center outward over 2.5 seconds
- [x] 6.3 Implement color ramp: #3b82f6 (low) → #fbbf24 (mid) → #ef4444 (high)
- [x] 6.4 Add pulsing glow on hot spots: 0.5Hz for 3 seconds after bloom completes
- [x] 6.5 Add mobile fallback: static image render below 768px breakpoint

## 7. Demo Page — Typewriter Explanation

- [x] 7.1 Build TypewriterText React island: character-by-character reveal at ~60ms per character
- [x] 7.2 Add attribution line: "Gemma 4 · VLM Explanation" above explanation
- [x] 7.3 Handle null/missing explanation with fallback message

## 8. Demo Page — Director Mode

- [x] 8.1 Implement director mode toggle: `D` key shows/hides "DIRECTOR" indicator
- [x] 8.2 Implement preset 1 (`1` key): Saree_000 → Saree_000, auto-catalog + verify (expected MATCH ~0.97)
- [x] 8.3 Implement preset 2 (`2` key): Saree_000 → Saree_005, auto-catalog + verify (expected SUSPECT ~0.58)
- [x] 8.4 Implement preset 3 (`3` key): Sherwani_001 → Saree_003, auto-catalog + verify (expected REJECT ~0.12)
- [x] 8.5 Implement animation speed control: `S` key = slow mode (bloom 5s, typewriter 120ms), `N` key = normal
- [x] 8.6 Implement "Replay" button: clears result, re-triggers last preset
- [x] 8.7 Load fixture images from `data/fixtures/{category}/{category}_{000-009}.jpg` via Astro static imports or public directory

## 9. Integration & Build

- [x] 9.1 Mount `frontend/dist/` as static files in FastAPI via `StaticFiles` middleware
- [x] 9.2 Configure Astro build output to `frontend/dist/` with correct base path
- [x] 9.3 Add build scripts: `build:frontend` (astro build), `dev:frontend` (astro dev)
- [ ] 9.4 End-to-end test: landing page loads static (zero JS), demo page verifies with real API, heatmap animates, director mode presets work
- [ ] 9.5 Test all 5 breakpoints: 375px, 768px, 1024px, 1440px, 1920px
- [ ] 9.6 Test video recording workflow: 1920px browser, director mode, preset 2 → SUSPECT result with heatmap bloom + typewriter
