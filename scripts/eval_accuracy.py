#!/usr/bin/env python3
"""Statistical accuracy evaluation for VerifAI verification pipeline.

Phases:
  A — Encode all 40 fixture images (pooled + tokens + CLAHE + baselines)
  B — Pairwise evaluation with replicated decision logic (no Gemma calls)
  C — Metrics: confusion matrix, per-category, ROC curve, hard cases
  D — Save JSON results + print summary

Usage:
    cd repo && uv run python scripts/eval_accuracy.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import torch
from torch.nn.functional import cosine_similarity

# ── Project root ────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
IMAGES_DIR = FIXTURES_DIR / "images"
OUTPUT_DIR = REPO_ROOT / "scripts" / "eval_results"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Constants (mirrors verify_return.py) ────────────────────────
DEFAULT_THRESHOLD = 0.7
DEFAULT_REGIONAL_THRESHOLD = 0.25
DEFAULT_DELTA_THRESHOLD = 0.15
HEATMAP_GRID = 16


# ================================================================
# Phase A: Encode all images
# ================================================================


def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        logger.error(
            "No manifest at %s — run scripts/download_fixtures.py first.",
            MANIFEST_PATH,
        )
        sys.exit(1)
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def load_images(manifest: list[dict]) -> dict[str, dict]:
    """Load all images indexed by stem (e.g. ``saree_000``)."""
    from PIL import Image

    images: dict[str, dict] = {}
    for entry in manifest:
        img_path = FIXTURES_DIR / entry["image_path"]
        if not img_path.exists():
            logger.warning("Missing image: %s", img_path)
            continue
        image_id = Path(entry["image_path"]).stem
        images[image_id] = {
            "image": Image.open(img_path).convert("RGB"),
            "category": entry["category"],
            "brand": entry.get("brand", ""),
            "product_title": entry.get("product_title", ""),
        }
    return images


def encode_all_images(
    encoder,
    images: dict[str, dict],
) -> dict[str, dict]:
    """Encode every image: pooled, tokens, CLAHE tokens, baseline."""
    from app.application.use_cases.verify_helpers import compute_baseline
    from app.infrastructure.ijepa_encoder import normalize_clahe

    encoded: dict[str, dict] = {}
    total = len(images)
    t0 = time.perf_counter()

    for idx, (image_id, meta) in enumerate(images.items()):
        img = meta["image"]
        img_np = np.array(img)

        pooled, tokens = encoder.encode_image(img, return_tokens=True)

        clahe_img = normalize_clahe(img_np)
        _, clahe_tokens = encoder.encode_image(clahe_img, return_tokens=True)

        baseline = compute_baseline(encoder, pooled.numpy(), img)

        encoded[image_id] = {
            "pooled": pooled,
            "tokens": tokens,
            "clahe_tokens": clahe_tokens,
            "baseline": baseline,
            "category": meta["category"],
            "brand": meta["brand"],
            "product_title": meta["product_title"],
        }

        if (idx + 1) % 10 == 0 or idx == total - 1:
            logger.info("Encoded %d/%d images (%.1fs)", idx + 1, total, time.perf_counter() - t0)

    return encoded


# ================================================================
# Decision logic — mirrors verify_return.py, no LLM
# ================================================================


def _compute_regional_stats(
    tokens_a: torch.Tensor,
    tokens_b: torch.Tensor,
    regional_threshold: float,
) -> tuple[np.ndarray, int, int]:
    """Replicate ``SpatialDiff.compute_regional_stats``."""
    sims = cosine_similarity(tokens_a, tokens_b, dim=-1)
    diff_scores = 1.0 - sims.numpy()
    heatmap = diff_scores.reshape(HEATMAP_GRID, HEATMAP_GRID)
    flagged = heatmap > regional_threshold
    flagged_count = int(flagged.sum())
    contiguous_regions = _count_contiguous(flagged)
    return heatmap, flagged_count, contiguous_regions


def _compute_patch_deltas(
    raw_tokens: torch.Tensor,
    norm_tokens: torch.Tensor,
    catalog_tokens: torch.Tensor,
) -> np.ndarray:
    """Replicate ``compute_patch_deltas``."""
    raw_sims = cosine_similarity(raw_tokens, catalog_tokens, dim=-1)
    norm_sims = cosine_similarity(norm_tokens, catalog_tokens, dim=-1)
    deltas = (norm_sims - raw_sims).numpy()
    return deltas.reshape(HEATMAP_GRID, HEATMAP_GRID)


def _count_contiguous(flagged: np.ndarray) -> int:
    visited = np.zeros_like(flagged, dtype=bool)
    regions = 0
    for i in range(flagged.shape[0]):
        for j in range(flagged.shape[1]):
            if flagged[i, j] and not visited[i, j]:
                _flood_fill(flagged, visited, i, j)
                regions += 1
    return regions


def _flood_fill(grid: np.ndarray, visited: np.ndarray, i: int, j: int) -> None:
    stack = [(i, j)]
    while stack:
        ci, cj = stack.pop()
        if ci < 0 or ci >= grid.shape[0] or cj < 0 or cj >= grid.shape[1]:
            continue
        if visited[ci, cj] or not grid[ci, cj]:
            continue
        visited[ci, cj] = True
        stack.extend([(ci - 1, cj), (ci + 1, cj), (ci, cj - 1), (ci, cj + 1)])


def evaluate_pair(
    catalog_id: str,
    return_id: str,
    encoded: dict[str, dict],
) -> dict:
    """Evaluate a single pair using pre-computed embeddings (no LLM)."""
    cat = encoded[catalog_id]
    ret = encoded[return_id]

    baseline = cat["baseline"]
    product_threshold = baseline.threshold
    regional_threshold = baseline.regional_threshold
    delta_threshold = baseline.delta_threshold

    score = cosine_similarity(
        cat["pooled"].unsqueeze(0),
        ret["pooled"].unsqueeze(0),
    ).item()

    result: dict = {
        "catalog_id": catalog_id,
        "return_id": return_id,
        "catalog_category": cat["category"],
        "return_category": ret["category"],
        "catalog_brand": cat["brand"],
        "return_brand": ret["brand"],
        "score": round(score, 6),
        "decision": "MATCH",
        "suspect_reason": None,
        "would_call_llm": False,
        "contiguous_regions": 0,
        "flagged_count": 0,
        "max_delta": None,
    }

    # ── REJECT path (low similarity) ─────────────────────────
    if score < product_threshold:
        result["decision"] = "REJECT"
        result["would_call_llm"] = True
        return result

    # ── Spatial diff check ───────────────────────────────────
    heatmap, flagged_count, contiguous_regions = _compute_regional_stats(
        cat["tokens"], ret["tokens"], regional_threshold,
    )
    result["contiguous_regions"] = contiguous_regions
    result["flagged_count"] = flagged_count

    if contiguous_regions >= 2:
        # SUSPECT path — CLAHE augmentation consistency test
        deltas = _compute_patch_deltas(
            ret["tokens"], ret["clahe_tokens"], cat["tokens"],
        )
        max_delta = float(np.max(deltas))
        result["max_delta"] = round(max_delta, 6)

        if max_delta > delta_threshold:
            result["decision"] = "MATCH"
            result["suspect_reason"] = "LIGHTING_ARTIFACT"
        elif max_delta < delta_threshold * 0.33:
            result["decision"] = "REJECT"
            result["suspect_reason"] = "CONTENT_DIFF"
            result["would_call_llm"] = True
        else:
            # Ambiguous → would ask Gemma
            result["decision"] = "SUSPECT"
            result["would_call_llm"] = True
        return result

    # ── Clean MATCH ──────────────────────────────────────────
    return result


# ================================================================
# Phase B: Pair generation
# ================================================================


def generate_pairs(
    encoded: dict[str, dict],
) -> list[tuple[str, str, str]]:
    """Generate test pairs tagged by type.

    Returns list of ``(catalog_id, return_id, pair_type)`` where
    *pair_type* is ``genuine``, ``same_category``, or ``cross_category``.
    """
    by_category: dict[str, list[str]] = defaultdict(list)
    for image_id, meta in encoded.items():
        by_category[meta["category"]].append(image_id)

    categories = sorted(by_category.keys())
    pairs: list[tuple[str, str, str]] = []

    # 1) Genuine — each image vs itself → expect MATCH
    for image_id in sorted(encoded.keys()):
        pairs.append((image_id, image_id, "genuine"))

    # 2) Same-category — different images, same category
    for cat in categories:
        ids = sorted(by_category[cat])
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append((ids[i], ids[j], "same_category"))

    # 3) Cross-category — different categories → expect REJECT
    for c1, c2 in combinations(categories, 2):
        for id1 in sorted(by_category[c1]):
            for id2 in sorted(by_category[c2]):
                pairs.append((id1, id2, "cross_category"))

    logger.info(
        "Generated %d pairs (%d genuine, %d same_category, %d cross_category)",
        len(pairs),
        sum(1 for _, _, t in pairs if t == "genuine"),
        sum(1 for _, _, t in pairs if t == "same_category"),
        sum(1 for _, _, t in pairs if t == "cross_category"),
    )
    return pairs


# ================================================================
# Phase C: Metrics computation
# ================================================================


def _tag_expected(results: list[dict]) -> None:
    """Set ``expected`` field on each result for metrics."""
    for r in results:
        ptype = r["pair_type"]
        if ptype == "genuine":
            r["expected"] = "MATCH"
        elif ptype == "cross_category":
            r["expected"] = "REJECT"
        else:
            # same_category — mark as MATCH expected (same garment type)
            # but flag counterfeit if brands differ
            r["expected"] = "MATCH"
            r["is_counterfeit"] = r["catalog_brand"] != r["return_brand"]


def compute_metrics(results: list[dict]) -> dict:
    _tag_expected(results)

    # ── Overall confusion matrix (genuine + cross_category only) ──
    clear = [r for r in results if r["pair_type"] in ("genuine", "cross_category")]
    tp = sum(1 for r in clear if r["expected"] == "MATCH" and r["decision"] == "MATCH")
    tn = sum(1 for r in clear if r["expected"] == "REJECT" and r["decision"] == "REJECT")
    fp = sum(1 for r in clear if r["expected"] == "REJECT" and r["decision"] == "MATCH")
    fn = sum(1 for r in clear if r["expected"] == "MATCH" and r["decision"] == "REJECT")
    total_clear = len(clear)
    accuracy = (tp + tn) / total_clear if total_clear else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    llm_calls = sum(1 for r in results if r["would_call_llm"])

    # ── Per-category metrics ──────────────────────────────────
    categories = sorted({r["catalog_category"] for r in results})
    per_category: dict[str, dict] = {}
    for cat in categories:
        cr = [r for r in clear if r["catalog_category"] == cat]
        ctp = sum(1 for r in cr if r["expected"] == "MATCH" and r["decision"] == "MATCH")
        ctn = sum(1 for r in cr if r["expected"] == "REJECT" and r["decision"] == "REJECT")
        cfp = sum(1 for r in cr if r["expected"] == "REJECT" and r["decision"] == "MATCH")
        cfn = sum(1 for r in cr if r["expected"] == "MATCH" and r["decision"] == "REJECT")
        ct = len(cr)
        per_category[cat] = {
            "total_pairs": ct,
            "tp": ctp, "tn": ctn, "fp": cfp, "fn": cfn,
            "accuracy": round((ctp + ctn) / ct, 4) if ct else 0.0,
        }

    # ── By pair type stats ────────────────────────────────────
    by_type: dict[str, dict] = {}
    for ptype in ("genuine", "same_category", "cross_category"):
        tr = [r for r in results if r["pair_type"] == ptype]
        if not tr:
            continue
        scores = [r["score"] for r in tr]
        decisions = defaultdict(int)
        for r in tr:
            decisions[r["decision"]] += 1
        by_type[ptype] = {
            "total": len(tr),
            "avg_score": round(float(np.mean(scores)), 4),
            "min_score": round(min(scores), 4),
            "max_score": round(max(scores), 4),
            "std_score": round(float(np.std(scores)), 4),
            "llm_calls": sum(1 for r in tr if r["would_call_llm"]),
            "decisions": dict(decisions),
        }

    # ── Counterfeit vs same-brand within same_category ───────
    same_cat = [r for r in results if r["pair_type"] == "same_category"]
    counterfeit = [r for r in same_cat if r.get("is_counterfeit")]
    same_brand = [r for r in same_cat if not r.get("is_counterfeit")]

    def _sub_stats(subset: list[dict]) -> dict:
        if not subset:
            return {}
        scores = [r["score"] for r in subset]
        decisions = defaultdict(int)
        for r in subset:
            decisions[r["decision"]] += 1
        return {
            "total": len(subset),
            "avg_score": round(float(np.mean(scores)), 4),
            "min_score": round(min(scores), 4),
            "max_score": round(max(scores), 4),
            "std_score": round(float(np.std(scores)), 4),
            "decisions": dict(decisions),
        }

    # ── ROC curve: sweep threshold over cosine scores ─────────
    roc_data: list[dict] = []
    for t_100 in range(50, 100, 5):
        t = t_100 / 100.0
        tp_t = sum(1 for r in clear if r["expected"] == "MATCH" and r["score"] >= t)
        tn_t = sum(1 for r in clear if r["expected"] == "REJECT" and r["score"] < t)
        fp_t = sum(1 for r in clear if r["expected"] == "REJECT" and r["score"] >= t)
        fn_t = sum(1 for r in clear if r["expected"] == "MATCH" and r["score"] < t)
        acc_t = (tp_t + tn_t) / total_clear if total_clear else 0.0
        prec_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) else 0.0
        rec_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) else 0.0
        fpr_t = fp_t / (fp_t + tn_t) if (fp_t + tn_t) else 0.0
        roc_data.append({
            "threshold": t,
            "accuracy": round(acc_t, 4),
            "precision": round(prec_t, 4),
            "recall": round(rec_t, 4),
            "fpr": round(fpr_t, 4),
        })

    # ── Hard cases: closest to decision boundary ──────────────
    hard_cases: list[dict] = []
    genuine_res = sorted(
        [r for r in results if r["pair_type"] == "genuine"],
        key=lambda r: r["score"],
    )
    hard_cases.extend([
        {
            "kind": "genuine_lowest",
            "catalog_id": r["catalog_id"],
            "return_id": r["return_id"],
            "score": r["score"],
            "decision": r["decision"],
        }
        for r in genuine_res[:5]
    ])
    cross_res = sorted(
        [r for r in results if r["pair_type"] == "cross_category"],
        key=lambda r: -r["score"],
    )
    hard_cases.extend([
        {
            "kind": "cross_highest",
            "catalog_id": r["catalog_id"],
            "return_id": r["return_id"],
            "score": r["score"],
            "decision": r["decision"],
        }
        for r in cross_res[:5]
    ])

    # ── False positives / negatives detail ────────────────────
    false_positives = [
        {"catalog_id": r["catalog_id"], "return_id": r["return_id"],
         "score": r["score"], "pair_type": r["pair_type"]}
        for r in clear
        if r["expected"] == "REJECT" and r["decision"] == "MATCH"
    ]
    false_negatives = [
        {"catalog_id": r["catalog_id"], "return_id": r["return_id"],
         "score": r["score"], "pair_type": r["pair_type"]}
        for r in clear
        if r["expected"] == "MATCH" and r["decision"] == "REJECT"
    ]

    return {
        "overall": {
            "total_pairs": len(results),
            "evaluated_pairs": total_clear,
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "llm_call_rate": round(llm_calls / len(results), 4) if results else 0.0,
            "llm_calls": llm_calls,
        },
        "per_category": per_category,
        "by_pair_type": by_type,
        "counterfeit_analysis": _sub_stats(counterfeit),
        "same_brand_analysis": _sub_stats(same_brand),
        "roc_data": roc_data,
        "hard_cases": hard_cases,
        "false_positives": false_positives[:20],
        "false_negatives": false_negatives[:20],
    }


# ================================================================
# Pretty-print
# ================================================================


def print_summary(metrics: dict) -> None:
    o = metrics["overall"]
    w = 72

    print("\n" + "=" * w)
    print("  VerifAI Accuracy Evaluation Summary")
    print("=" * w)

    print(f"\n{'Overall Metrics':^{w}}")
    print("-" * w)
    print(f"  Total pairs evaluated: {o['evaluated_pairs']} (of {o['total_pairs']} total)")
    print(f"  Accuracy:              {o['accuracy']:.2%}")
    print(f"  Precision:             {o['precision']:.2%}")
    print(f"  Recall:                {o['recall']:.2%}")
    print(f"  F1 Score:              {o['f1']:.2%}")
    print(f"  LLM call rate:         {o['llm_call_rate']:.2%}  ({o['llm_calls']}/{o['total_pairs']})")

    print(f"\n{'Confusion Matrix':^{w}}")
    print("-" * w)
    print(f"  TP (correct MATCH) :  {o['tp']:>5}")
    print(f"  TN (correct REJECT):  {o['tn']:>5}")
    print(f"  FP (wrong MATCH)   :  {o['fp']:>5}")
    print(f"  FN (wrong REJECT)  :  {o['fn']:>5}")

    print(f"\n{'Per-Category Accuracy':^{w}}")
    print("-" * w)
    hdr = f"  {'Category':<12} {'Pairs':>6} {'TP':>5} {'TN':>5} {'FP':>5} {'FN':>5} {'Accuracy':>10}"
    print(hdr)
    for cat, cm in sorted(metrics["per_category"].items()):
        print(f"  {cat:<12} {cm['total_pairs']:>6} {cm['tp']:>5} {cm['tn']:>5} "
              f"{cm['fp']:>5} {cm['fn']:>5} {cm['accuracy']:>9.2%}")

    print(f"\n{'By Pair Type':^{w}}")
    print("-" * w)
    for ptype, data in metrics["by_pair_type"].items():
        print(f"  {ptype}:")
        print(f"    Count: {data['total']}   "
              f"Avg score: {data['avg_score']:.4f}   "
              f"Std: {data['std_score']:.4f}   "
              f"Range: [{data['min_score']:.4f}, {data['max_score']:.4f}]")
        print(f"    Decisions: {data['decisions']}   LLM calls: {data['llm_calls']}")

    ca = metrics.get("counterfeit_analysis") or {}
    if ca:
        print(f"\n{'Counterfeit (diff brand, same category)':^{w}}")
        print("-" * w)
        print(f"  Pairs: {ca['total']}   Avg score: {ca['avg_score']:.4f}   "
              f"Range: [{ca['min_score']:.4f}, {ca['max_score']:.4f}]")
        print(f"  Decisions: {ca['decisions']}")

    sa = metrics.get("same_brand_analysis") or {}
    if sa:
        print(f"\n{'Same Brand (same category)':^{w}}")
        print("-" * w)
        print(f"  Pairs: {sa['total']}   Avg score: {sa['avg_score']:.4f}   "
              f"Range: [{sa['min_score']:.4f}, {sa['max_score']:.4f}]")
        print(f"  Decisions: {sa['decisions']}")

    print(f"\n{'Threshold Sweep':^{w}}")
    print("-" * w)
    print(f"  {'Thresh':>7} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'FPR':>10}")
    best = max(metrics["roc_data"], key=lambda x: x["accuracy"])
    for pt in metrics["roc_data"]:
        tag = " <- best" if pt["threshold"] == best["threshold"] else ""
        print(f"  {pt['threshold']:>7.2f} {pt['accuracy']:>9.2%} {pt['precision']:>9.2%} "
              f"{pt['recall']:>9.2%} {pt['fpr']:>9.2%}{tag}")

    print(f"\n{'Hard Cases':^{w}}")
    print("-" * w)
    for hc in metrics.get("hard_cases", []):
        print(f"  [{hc['kind']}] {hc['catalog_id']} vs {hc['return_id']}  "
              f"score={hc['score']:.4f} -> {hc['decision']}")

    if metrics.get("false_positives"):
        print(f"\n{'False Positives (top 10)':^{w}}")
        print("-" * w)
        for fp in metrics["false_positives"][:10]:
            print(f"  {fp['catalog_id']} vs {fp['return_id']}  "
                  f"score={fp['score']:.4f}  ({fp['pair_type']})")

    if metrics.get("false_negatives"):
        print(f"\n{'False Negatives (top 10)':^{w}}")
        print("-" * w)
        for fn in metrics["false_negatives"][:10]:
            print(f"  {fn['catalog_id']} vs {fn['return_id']}  "
                  f"score={fn['score']:.4f}  ({fn['pair_type']})")

    print("\n" + "=" * w)


# ================================================================
# Main
# ================================================================


def main() -> None:
    t_start = time.perf_counter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Phase A ──────────────────────────────────────────────
    logger.info("Phase A: Loading and encoding images...")
    manifest = load_manifest()
    images = load_images(manifest)
    logger.info("Loaded %d images from manifest", len(images))

    from app.infrastructure.ijepa_encoder import IjepaEncoder

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Device: %s", device)
    encoder = IjepaEncoder(device=device)

    encoded = encode_all_images(encoder, images)
    t_encode = time.perf_counter()
    logger.info("Phase A done (%.1fs)", t_encode - t_start)

    # ── Phase B ──────────────────────────────────────────────
    logger.info("Phase B: Pairwise evaluation...")
    pairs = generate_pairs(encoded)

    results: list[dict] = []
    for i, (cat_id, ret_id, ptype) in enumerate(pairs):
        r = evaluate_pair(cat_id, ret_id, encoded)
        r["pair_type"] = ptype
        r["is_counterfeit"] = (
            ptype == "same_category"
            and encoded[cat_id]["brand"] != encoded[ret_id]["brand"]
        )
        results.append(r)
        if (i + 1) % 200 == 0:
            logger.info("  %d/%d pairs evaluated...", i + 1, len(pairs))

    t_eval = time.perf_counter()
    logger.info("Phase B done (%.1fs, %d pairs)", t_eval - t_encode, len(results))

    # ── Phase C ──────────────────────────────────────────────
    logger.info("Phase C: Computing metrics...")
    metrics = compute_metrics(results)
    print_summary(metrics)

    # ── Save ─────────────────────────────────────────────────
    results_path = OUTPUT_DIR / "eval_results.json"
    summary_path = OUTPUT_DIR / "eval_summary.json"

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    with open(summary_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    t_total = time.perf_counter() - t_start
    logger.info("Total: %.1fs", t_total)
    print(f"\nResults saved to {OUTPUT_DIR}/")
    print(f"  eval_results.json  ({len(results)} pairs)")
    print(f"  eval_summary.json  (aggregated metrics)")


if __name__ == "__main__":
    main()
