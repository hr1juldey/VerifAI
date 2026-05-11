"""
Library for recording individual segments as PNG frames.
Each frame is a lossless screenshot — no codec crushing dark gradients.

Updated for new narration (19 chunks, ~199s total).
Audio durations: hero=25.6s, obstacle=61.7s, outcome=34.0s,
                 insight=45.2s, demo=21.4s, close=10.8s
"""

import os
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
FIXTURES = "/home/riju279/Documents/Code/Jepa/VerifAI/frontend/public/fixtures"
FRAMES_DIR = "/home/riju279/Documents/Code/Jepa/VerifAI/scripts/video/segments/frames"
os.makedirs(FRAMES_DIR, exist_ok=True)

VIEWPORT = {"width": 1920, "height": 1080}
FPS = 30


def smooth_scroll(page, target_y, duration_ms=1500):
    page.evaluate(f"window.scrollTo({{ top: {target_y}, behavior: 'smooth' }})")
    page.wait_for_timeout(duration_ms)


class FrameRecorder:
    """Takes a screenshot every frame_interval_ms, saves as PNG."""

    def __init__(self, page, segment_name, fps=FPS):
        self.page = page
        self.seg_dir = os.path.join(FRAMES_DIR, segment_name)
        os.makedirs(self.seg_dir, exist_ok=True)
        # Clear old frames
        for f in os.listdir(self.seg_dir):
            if f.endswith('.png'):
                os.remove(os.path.join(self.seg_dir, f))
        self.frame_num = 0
        self.interval = int(1000 / fps)

    def capture(self):
        path = os.path.join(self.seg_dir, f"frame_{self.frame_num:06d}.png")
        self.page.screenshot(path=path)
        self.frame_num += 1

    def wait_and_capture(self, duration_ms):
        """Capture frames at FPS for the given duration."""
        frames_to_take = int(duration_ms / self.interval)
        for _ in range(frames_to_take):
            self.page.wait_for_timeout(self.interval)
            self.capture()

    def wait_quiet(self, duration_ms):
        """Just wait without capturing (for transitions)."""
        self.page.wait_for_timeout(duration_ms)


def record_one_segment(segment_name):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport=VIEWPORT)
    page = ctx.new_page()
    rec = FrameRecorder(page, segment_name)

    SEGMENTS = {
        "seg1_hero": segment_hero,
        "seg2_obstacle": segment_obstacle,
        "seg3_outcome": segment_outcome,
        "seg4_insight": segment_insight,
        "seg5_demo": segment_demo,
        "seg6_close": segment_close,
    }

    fn = SEGMENTS.get(segment_name)
    if fn:
        fn(page, rec)
    else:
        print(f"Unknown segment: {segment_name}")

    page.close()
    ctx.close()
    browser.close()
    p.stop()

    frame_count = len([f for f in os.listdir(rec.seg_dir) if f.endswith('.png')])
    print(f"[{segment_name}] Captured {frame_count} frames")


# ── SEGMENT FUNCTIONS ───────────────────────────────────────────

def segment_hero(page, rec):
    """25.6s — Landing page hero animation."""
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)  # Let React hydrate + hero animation start

    # Record the hero section animation
    rec.wait_and_capture(22600)


def segment_obstacle(page, rec):
    """61.7s — Pain points: return fraud stats, costs, current solutions."""
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    # Start at hero, let it breathe
    rec.wait_and_capture(5000)

    # Scroll to pain/stats section
    smooth_scroll(page, page.evaluate("document.body.scrollHeight") * 0.3, 1500)
    rec.wait_and_capture(8000)

    # Continue scrolling through pain content
    smooth_scroll(page, page.evaluate("document.body.scrollHeight") * 0.5, 1500)
    rec.wait_and_capture(8000)

    # Scroll to technology section
    smooth_scroll(page, page.evaluate("document.body.scrollHeight") * 0.7, 1500)
    rec.wait_and_capture(8000)

    # More tech / problem context
    smooth_scroll(page, page.evaluate("document.body.scrollHeight") * 0.85, 1200)
    rec.wait_and_capture(10000)

    # Current solutions — hold
    rec.wait_and_capture(8000)


def segment_outcome(page, rec):
    """34.0s — What would it take? Classifier won't work. Need understanding."""
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    # Jump to mid-page where tech discussion is
    page.evaluate("window.scrollTo({ top: document.body.scrollHeight * 0.4, behavior: 'smooth' })")
    page.wait_for_timeout(2000)

    rec.wait_and_capture(10000)

    # Slow scroll through technology explanation
    smooth_scroll(page, page.evaluate("window.scrollY") + 250, 2000)
    rec.wait_and_capture(12000)

    # Hold on the key insight
    smooth_scroll(page, page.evaluate("window.scrollY") + 200, 1500)
    rec.wait_and_capture(3500)


def segment_insight(page, rec):
    """45.2s — I-JEPA explanation, representations, 10 photos, runs on cheap GPU."""
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    # Scroll to technology/architecture section
    page.evaluate("window.scrollTo({ top: document.body.scrollHeight * 0.5, behavior: 'smooth' })")
    page.wait_for_timeout(2500)

    rec.wait_and_capture(12000)

    # Continue through architecture details
    smooth_scroll(page, page.evaluate("window.scrollY") + 300, 2000)
    rec.wait_and_capture(10000)

    # The "10 photos" and GPU part
    smooth_scroll(page, page.evaluate("window.scrollY") + 250, 1500)
    rec.wait_and_capture(8000)

    # Hold on GPU/practical section
    smooth_scroll(page, page.evaluate("window.scrollY") + 200, 1200)
    rec.wait_and_capture(5000)


def segment_demo(page, rec):
    """21.4s — Live demo: swap fraud, match, completely wrong product."""
    page.goto(f"{BASE_URL}/demo")
    page.wait_for_timeout(3000)

    # Fill in product ID
    page.locator("input[type='text']").fill("Saree_000")
    page.wait_for_timeout(500)

    file_inputs = page.locator("input[type='file']")

    # CASE 1: Swap fraud — different shaari
    file_inputs.nth(0).set_input_files(os.path.join(FIXTURES, "saree", "saree_000.jpeg"))
    rec.wait_and_capture(1500)

    file_inputs.nth(1).set_input_files(os.path.join(FIXTURES, "saree", "saree_005.jpeg"))
    rec.wait_and_capture(1500)

    verify_btn = page.locator("button:has-text('Verify Return')")
    page.wait_for_timeout(500)
    try:
        verify_btn.click(timeout=3000)
    except Exception:
        verify_btn.click(force=True)
    rec.wait_and_capture(3000)

    # CASE 2: MATCH — same product
    page.reload()
    page.wait_for_timeout(2000)
    page.locator("input[type='text']").fill("Saree_002")
    page.wait_for_timeout(500)
    file_inputs = page.locator("input[type='file']")
    same = os.path.join(FIXTURES, "saree", "saree_002.jpeg")
    file_inputs.nth(0).set_input_files(same)
    rec.wait_and_capture(1000)
    file_inputs.nth(1).set_input_files(same)
    rec.wait_and_capture(1000)
    verify_btn = page.locator("button:has-text('Verify Return')")
    page.wait_for_timeout(500)
    try:
        verify_btn.click(timeout=3000)
    except Exception:
        verify_btn.click(force=True)
    rec.wait_and_capture(2000)

    # CASE 3: FRAUD — completely wrong product
    page.reload()
    page.wait_for_timeout(2000)
    page.locator("input[type='text']").fill("Sherwani_vs_Saree")
    page.wait_for_timeout(500)
    file_inputs = page.locator("input[type='file']")
    file_inputs.nth(0).set_input_files(os.path.join(FIXTURES, "sherwani", "sherwani_000.jpeg"))
    rec.wait_and_capture(1000)
    file_inputs.nth(1).set_input_files(os.path.join(FIXTURES, "saree", "saree_003.jpeg"))
    rec.wait_and_capture(1000)
    verify_btn = page.locator("button:has-text('Verify Return')")
    page.wait_for_timeout(500)
    try:
        verify_btn.click(timeout=3000)
    except Exception:
        verify_btn.click(force=True)
    rec.wait_and_capture(1400)


def segment_close(page, rec):
    """10.8s — CTA + logo."""
    page.goto(BASE_URL)
    page.wait_for_timeout(2000)

    # Scroll to bottom — CTA section
    page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })")
    page.wait_for_timeout(3000)

    rec.wait_and_capture(5800)
