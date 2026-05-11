"""
Library module for recording individual segments in isolated processes.
Each call gets its own Playwright instance, avoiding event loop contamination.
"""

import os
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
FIXTURES = "/home/riju279/Documents/Code/Jepa/VerifAI/frontend/public/fixtures"
OUTPUT_DIR = "/home/riju279/Documents/Code/Jepa/VerifAI/scripts/video/segments/raw_video"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VIEWPORT = {"width": 1920, "height": 1080}


def smooth_scroll(page, target_y, duration_ms=1500):
    page.evaluate(f"window.scrollTo({{ top: {target_y}, behavior: 'smooth' }})")
    page.wait_for_timeout(duration_ms)


def record_one(segment_name):
    """Record a single segment in a fresh Playwright instance."""
    outpath = os.path.join(OUTPUT_DIR, f"{segment_name}.webm")

    # Clean any leftover temp webm files from failed previous runs
    # Only delete files that start with "page@" (Playwright's temp naming)
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("page@") and f.endswith(".webm"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except:
                pass

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=OUTPUT_DIR,
        record_video_size=VIEWPORT,
    )
    page = ctx.new_page()

    # Dispatch to segment function
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
        fn(page)
    else:
        print(f"Unknown segment: {segment_name}")

    page.close()
    ctx.close()

    # Rename Playwright's random file to our segment name
    # Playwright creates files named "page@<hash>.webm"
    renamed = False
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("page@") and f.endswith(".webm"):
            src = os.path.join(OUTPUT_DIR, f)
            if os.path.exists(outpath):
                os.remove(outpath)
            os.rename(src, outpath)
            renamed = True
            break

    browser.close()
    p.stop()
    if renamed:
        print(f"[{segment_name}] Saved: {outpath} ({os.path.getsize(outpath):,} bytes)")
    else:
        print(f"[{segment_name}] WARNING: no page@.webm file found to rename!")


# ── SEGMENT FUNCTIONS ───────────────────────────────────────────

def segment_hero(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)
    page.wait_for_timeout(26800)


def segment_obstacle(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    pain_el = page.locator("text=₹1,000+ Crore").first
    pain_el.scroll_into_view_if_needed()
    page.wait_for_timeout(2000)

    page.wait_for_timeout(8000)

    smooth_scroll(page, page.evaluate("window.scrollY") + 300)
    page.wait_for_timeout(8000)

    tech_el = page.locator("text=TECHNOLOGY").first
    tech_el.scroll_into_view_if_needed()
    page.wait_for_timeout(2000)

    page.wait_for_timeout(41200)


def segment_outcome(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    tech_el = page.locator("text=TECHNOLOGY").first
    tech_el.scroll_into_view_if_needed()
    page.wait_for_timeout(2000)

    page.wait_for_timeout(10000)

    smooth_scroll(page, page.evaluate("window.scrollY") + 200)
    page.wait_for_timeout(12000)

    page.wait_for_timeout(7200)


def segment_insight(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    tech_el = page.locator("text=TECHNOLOGY").first
    tech_el.scroll_into_view_if_needed()
    page.wait_for_timeout(3000)

    page.wait_for_timeout(20000)

    smooth_scroll(page, page.evaluate("window.scrollY") + 150)
    page.wait_for_timeout(12000)

    page.wait_for_timeout(12200)


def segment_demo(page):
    page.goto(f"{BASE_URL}/demo")
    page.wait_for_timeout(3000)

    # Button needs: productId text + catalogFile + returnFile
    # Fill the product ID text input first
    page.locator("input[type='text']").fill("Saree_000")
    page.wait_for_timeout(500)

    # CASE 1: Swap fraud — different sarees
    file_inputs = page.locator("input[type='file']")
    catalog_input = file_inputs.nth(0)
    return_input = file_inputs.nth(1)

    catalog_input.set_input_files(os.path.join(FIXTURES, "saree", "saree_000.jpeg"))
    page.wait_for_timeout(2000)

    return_input.set_input_files(os.path.join(FIXTURES, "saree", "saree_005.jpeg"))
    page.wait_for_timeout(2000)

    # Wait for button to be enabled, then click
    verify_btn = page.locator("button:has-text('Verify Return')")
    verify_btn.wait_for(state="visible", timeout=5000)
    # Force click in case React hasn't removed disabled attr yet
    page.wait_for_timeout(500)
    try:
        verify_btn.click(timeout=3000)
    except Exception:
        # Button might still be disabled — force it
        verify_btn.click(force=True)
    page.wait_for_timeout(6000)

    # CASE 2: MATCH — same image
    page.reload()
    page.wait_for_timeout(2000)
    page.locator("input[type='text']").fill("Saree_002")
    page.wait_for_timeout(500)
    file_inputs = page.locator("input[type='file']")
    same = os.path.join(FIXTURES, "saree", "saree_002.jpeg")
    file_inputs.nth(0).set_input_files(same)
    page.wait_for_timeout(1500)
    file_inputs.nth(1).set_input_files(same)
    page.wait_for_timeout(1500)
    verify_btn = page.locator("button:has-text('Verify Return')")
    page.wait_for_timeout(500)
    try:
        verify_btn.click(timeout=3000)
    except Exception:
        verify_btn.click(force=True)
    page.wait_for_timeout(4000)

    # CASE 3: FRAUD — completely different product
    page.reload()
    page.wait_for_timeout(2000)
    page.locator("input[type='text']").fill("Sherwani_vs_Saree")
    page.wait_for_timeout(500)
    file_inputs = page.locator("input[type='file']")
    file_inputs.nth(0).set_input_files(os.path.join(FIXTURES, "sherwani", "sherwani_000.jpeg"))
    page.wait_for_timeout(1500)
    file_inputs.nth(1).set_input_files(os.path.join(FIXTURES, "saree", "saree_003.jpeg"))
    page.wait_for_timeout(1500)
    verify_btn = page.locator("button:has-text('Verify Return')")
    page.wait_for_timeout(500)
    try:
        verify_btn.click(timeout=3000)
    except Exception:
        verify_btn.click(force=True)
    page.wait_for_timeout(5000)


def segment_close(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(2000)

    page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })")
    page.wait_for_timeout(3000)

    page.wait_for_timeout(7600)
