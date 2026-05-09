"""Download 40 fixture images from the Indo Fashion Kaggle dataset.

Usage:
    uv run python scripts/download_fixtures.py

Selects 10 images each from: saree, kurta, sherwani, lehenga.
Copies to tests/fixtures/images/ and writes tests/fixtures/manifest.json.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# Dataset uses these class_label values; we map to short names for fixtures
DATASET_CATEGORIES = {
    "saree": "saree",
    "women_kurta": "kurta",
    "sherwanis": "sherwani",
    "lehenga": "lehenga",
}
FIXTURE_CATEGORIES = list(DATASET_CATEGORIES.values())
IMAGES_PER_CATEGORY = 10
DATASET_HANDLE = "validmodel/indo-fashion-dataset"

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"


def main() -> None:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            existing = json.load(f)
        if len(existing) >= 40:
            print("Fixtures already exist. Delete tests/fixtures/ to re-download.")
            return

    print(f"Downloading dataset '{DATASET_HANDLE}' via kagglehub...")
    import kagglehub

    dataset_path = Path(kagglehub.dataset_download(DATASET_HANDLE))
    print(f"Dataset cached at: {dataset_path}")

    # Discover image directory
    images_root = dataset_path / "images"
    if not images_root.exists():
        # Fallback: find any images/ subdirectory
        candidates = list(dataset_path.rglob("images"))
        if candidates:
            images_root = candidates[0]
        else:
            raise FileNotFoundError(f"No images/ directory in {dataset_path}")

    # Load all JSONL metadata files (one JSON object per line)
    all_records: list[dict] = []
    for json_file in sorted(dataset_path.glob("*.json")):
        with open(json_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    all_records.append(json.loads(line))

    print(f"Found {len(all_records)} metadata records")

    # Group by category (map dataset labels to our fixture names)
    by_category: dict[str, list[dict]] = {}
    for rec in all_records:
        label = rec.get("class_label", "").lower()
        if label in DATASET_CATEGORIES:
            fixture_cat = DATASET_CATEGORIES[label]
            by_category.setdefault(fixture_cat, []).append(rec)

    for cat in FIXTURE_CATEGORIES:
        count = len(by_category.get(cat, []))
        print(f"  {cat}: {count} images available")

    # Select images
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for cat in FIXTURE_CATEGORIES:
        records = by_category.get(cat, [])
        if not records:
            print(f"WARNING: No images found for category '{cat}'")
            continue

        selected = records[:IMAGES_PER_CATEGORY]
        for i, rec in enumerate(selected):
            src_rel = rec.get("image_path", "")
            src = dataset_path / src_rel
            if not src.exists():
                # Try images_root / split / filename
                parts = src_rel.split("/")
                if len(parts) >= 2:
                    src = images_root / parts[-2] / parts[-1]
                if not src.exists():
                    print(f"  SKIP: {src_rel} not found")
                    continue

            dst_name = f"{cat}_{i:03d}{src.suffix}"
            dst = IMAGES_DIR / dst_name
            shutil.copy2(src, dst)

            manifest.append(
                {
                    "image_path": f"images/{dst_name}",
                    "category": cat,
                    "brand": rec.get("brand", ""),
                    "product_title": rec.get("product_title", ""),
                    "class_label": cat,
                }
            )

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone! {len(manifest)} images copied to {IMAGES_DIR}")
    print(f"Manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
