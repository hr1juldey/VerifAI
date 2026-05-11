"""
VerifAI Demo Video — Full Playwright Recording Script
Records all 6 segments as individual .webm videos, timed to match narration audio.
Run: python3.10 scripts/video/record_segments.py [seg_name ...]
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
FIXTURES = "/home/riju279/Documents/Code/Jepa/VerifAI/frontend/public/fixtures"
OUTPUT_DIR = "/home/riju279/Documents/Code/Jepa/VerifAI/scripts/video/segments/raw_video"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VIEWPORT = {"width": 1920, "height": 1080}

# Audio durations (measured via ffprobe)
SEGMENT_DURATIONS = {
    "seg1_hero": 29.8,
    "seg2_obstacle": 64.2,
    "seg3_outcome": 34.2,
    "seg4_insight": 50.2,
    "seg5_demo": 28.9,
    "seg6_close": 12.6,
}


def record_segment(segment_name: str, actions_fn):
    """Record one segment in a subprocess to avoid event loop contamination."""
    import subprocess
    target_dur = SEGMENT_DURATIONS.get(segment_name, "?")
    print(f"\n[{segment_name}] Recording ({target_dur}s target)...")

    # Write a temp script for this single segment
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_script = os.path.join(OUTPUT_DIR, f"_tmp_{segment_name}.py")
    with open(tmp_script, "w") as f:
        f.write(f"""
import os, sys
sys.path.insert(0, r'{script_dir}')
from record_segments_lib import record_one
record_one('{segment_name}')
""")
    
    result = subprocess.run(
        [sys.executable, tmp_script],
        capture_output=True, text=True, timeout=300
    )
    
    if os.path.exists(tmp_script):
        os.remove(tmp_script)
    
    outpath = os.path.join(OUTPUT_DIR, f"{segment_name}.webm")
    if os.path.exists(outpath):
        size = os.path.getsize(outpath)
        print(f"[{segment_name}] Done: {size:,} bytes")
    else:
        print(f"[{segment_name}] WARNING: output file not found")
        if result.stderr:
            print(f"[{segment_name}] stderr: {result.stderr[:500]}")


def smooth_scroll(page, target_y, duration_ms=1500):
    """Smooth scroll to a Y position."""
    page.evaluate(f"window.scrollTo({{ top: {target_y}, behavior: 'smooth' }})")
    page.wait_for_timeout(duration_ms)


# ── SEGMENT 1: HERO (29.8s) ────────────────────────────────────
def segment_hero(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)  # Page load + hero animation starts

    # Let the hero animation play through ~2 cycles
    # Each cycle: empty(1s) → catalog(2s) → return(2s) → scan(2s) → heatmap(2s) → verdict(2.5s) = ~11.5s
    page.wait_for_timeout(26800)


# ── SEGMENT 2: OBSTACLE (64.2s) ────────────────────────────────
def segment_obstacle(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    # Scroll to the "₹1,000+ Crore" pain section
    pain_el = page.locator("text=₹1,000+ Crore").first
    pain_el.scroll_into_view_if_needed()
    page.wait_for_timeout(2000)

    # Hold on pain stats — viewer absorbs 71%, ₹500-1000, 40%+
    page.wait_for_timeout(8000)

    # Slow scroll down to see all three stat cards fully
    smooth_scroll(page, page.evaluate("window.scrollY") + 300)
    page.wait_for_timeout(8000)

    # Scroll further to show the "TECHNOLOGY" area (the "failing solutions" text)
    tech_el = page.locator("text=TECHNOLOGY").first
    tech_el.scroll_into_view_if_needed()
    page.wait_for_timeout(2000)

    # Hold — let the viewer read
    page.wait_for_timeout(41200)


# ── SEGMENT 3: OUTCOME (34.2s) ─────────────────────────────────
def segment_outcome(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    # Scroll to TECHNOLOGY section
    tech_el = page.locator("text=TECHNOLOGY").first
    tech_el.scroll_into_view_if_needed()
    page.wait_for_timeout(2000)

    # Hold on "I-JEPA · ViT-H/14 · 632M parameters"
    page.wait_for_timeout(10000)

    # Scroll slightly to show the tech tag pills
    smooth_scroll(page, page.evaluate("window.scrollY") + 200)
    page.wait_for_timeout(12000)

    # Hold on tech tags
    page.wait_for_timeout(7200)


# ── SEGMENT 4: KEY INSIGHT (50.2s) ─────────────────────────────
def segment_insight(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    # Scroll to TECHNOLOGY section
    tech_el = page.locator("text=TECHNOLOGY").first
    tech_el.scroll_into_view_if_needed()
    page.wait_for_timeout(3000)

    # Hold on tech section — the I-JEPA explanation plays over this
    page.wait_for_timeout(20000)

    # Subtle scroll to keep it visually dynamic
    smooth_scroll(page, page.evaluate("window.scrollY") + 150)
    page.wait_for_timeout(12000)

    # Hold
    page.wait_for_timeout(12200)


# ── SEGMENT 5: THE DEMO (28.9s) ────────────────────────────────
def segment_demo(page):
    page.goto(f"{BASE_URL}/demo")
    page.wait_for_timeout(3000)

    # CASE 1: Swap fraud — different sarees
    file_inputs = page.locator("input[type='file']")
    catalog_input = file_inputs.nth(0)
    return_input = file_inputs.nth(1)

    catalog_input.set_input_files(os.path.join(FIXTURES, "saree", "saree_000.jpeg"))
    page.wait_for_timeout(2000)

    return_input.set_input_files(os.path.join(FIXTURES, "saree", "saree_005.jpeg"))
    page.wait_for_timeout(2000)

    # Click Verify Return
    page.locator("button:has-text('Verify Return')").click()
    page.wait_for_timeout(6000)  # Wait for API call + heatmap + verdict

    # CASE 2: MATCH — same image
    page.reload()
    page.wait_for_timeout(2000)
    file_inputs = page.locator("input[type='file']")
    same = os.path.join(FIXTURES, "saree", "saree_002.jpeg")
    file_inputs.nth(0).set_input_files(same)
    page.wait_for_timeout(1500)
    file_inputs.nth(1).set_input_files(same)
    page.wait_for_timeout(1500)
    page.locator("button:has-text('Verify Return')").click()
    page.wait_for_timeout(4000)

    # CASE 3: FRAUD — completely different product
    page.reload()
    page.wait_for_timeout(2000)
    file_inputs = page.locator("input[type='file']")
    file_inputs.nth(0).set_input_files(os.path.join(FIXTURES, "sherwani", "sherwani_000.jpeg"))
    page.wait_for_timeout(1500)
    file_inputs.nth(1).set_input_files(os.path.join(FIXTURES, "saree", "saree_003.jpeg"))
    page.wait_for_timeout(1500)
    page.locator("button:has-text('Verify Return')").click()
    page.wait_for_timeout(5000)


# ── SEGMENT 6: CLOSE (12.6s) ───────────────────────────────────
def segment_close(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(2000)

    # Scroll to early access form at bottom
    page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })")
    page.wait_for_timeout(3000)

    # Hold on form
    page.wait_for_timeout(7600)


# ── MAIN ────────────────────────────────────────────────────────
if __name__ == "__main__":
    segments = [
        ("seg1_hero", segment_hero),
        ("seg2_obstacle", segment_obstacle),
        ("seg3_outcome", segment_outcome),
        ("seg4_insight", segment_insight),
        ("seg5_demo", segment_demo),
        ("seg6_close", segment_close),
    ]

    if len(sys.argv) > 1:
        names = sys.argv[1:]
        segments = [(n, fn) for n, fn in segments if n in names]

    print(f"Recording {len(segments)} segment(s)...")
    for name, fn in segments:
        try:
            record_segment(name, fn)
        except Exception as e:
            print(f"[{name}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            # Clean up partial video
            for f in os.listdir(OUTPUT_DIR):
                if f.endswith(".webm") and name not in f:
                    os.remove(os.path.join(OUTPUT_DIR, f))

    print(f"\nAll {len(segments)} segment(s) recorded. Output in {OUTPUT_DIR}")
