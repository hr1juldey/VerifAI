#!/usr/bin/env python3
"""End-to-end accuracy evaluation via the VerifAI REST API.

Hits the real FastAPI server (POST /catalog + POST /verify) instead of
importing Python classes directly.  This surfaces HTTP-layer bugs,
serialization issues, memory behaviour, and the true production path.

Usage:
    # 1. Start the server in a separate terminal / tmux:
    cd repo && uv run uvicorn app.presentation.main:app --host 127.0.0.1 --port 8000

    # 2. Run the e2e eval (sample mode):
    uv run python scripts/eval_e2e.py --base-url http://127.0.0.1:8000

    # 3. Full 820-pair run (takes ~2+ hours):
    uv run python scripts/eval_e2e.py --full

    # 4. Custom sample size:
    uv run python scripts/eval_e2e.py --sample-size 60
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import httpx

# ── Project root ────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
MANIFEST_PATH = FIXTURES_DIR / "images" / "manifest.json"
OUTPUT_DIR = REPO_ROOT / "scripts" / "eval_results"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Sampling defaults ───────────────────────────────────────────
DEFAULT_SAMPLE_SIZE = 60
CATALOG_TIMEOUT = 30
VERIFY_TIMEOUT = 120


# ================================================================
# 1. Load manifest
# ================================================================
def load_manifest() -> list[dict]:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


# ================================================================
# 2. Pair generation
# ================================================================
def generate_pairs(manifest: list[dict]) -> list[dict]:
    """Generate all pairwise combinations with expected labels."""
    categories: dict[str, list[dict]] = {}
    for item in manifest:
        categories.setdefault(item["category"], []).append(item)

    pairs = []
    cat_names = sorted(categories.keys())

    # Genuine: each image vs itself -> expect MATCH
    for items in categories.values():
        for item in items:
            pairs.append({
                "catalog_id": item["product_id"],
                "return_id": item["product_id"],
                "catalog_category": item["category"],
                "return_category": item["category"],
                "pair_type": "genuine",
                "expected": "MATCH",
            })

    # Same-category: different images -> expect REJECT (counterfeit)
    for items in categories.values():
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                pairs.append({
                    "catalog_id": a["product_id"],
                    "return_id": b["product_id"],
                    "catalog_category": a["category"],
                    "return_category": b["category"],
                    "pair_type": "same_category",
                    "expected": "REJECT",
                })

    # Cross-category: different categories -> expect REJECT
    for i, c1 in enumerate(cat_names):
        for c2 in cat_names[i + 1:]:
            for a in categories[c1]:
                for b in categories[c2]:
                    pairs.append({
                        "catalog_id": a["product_id"],
                        "return_id": b["product_id"],
                        "catalog_category": c1,
                        "return_category": c2,
                        "pair_type": "cross_category",
                        "expected": "REJECT",
                    })

    return pairs


def stratified_sample(pairs: list[dict], n: int) -> list[dict]:
    """Pick *n* pairs stratified by pair_type."""
    by_type: dict[str, list[dict]] = {}
    for p in pairs:
        by_type.setdefault(p["pair_type"], []).append(p)

    allocated = {
        "genuine": min(len(by_type.get("genuine", [])), max(10, n // 6)),
        "same_category": min(len(by_type.get("same_category", [])), n // 3),
        "cross_category": min(len(by_type.get("cross_category", [])), n // 2),
    }

    sampled = []
    for ptype, count in allocated.items():
        group = by_type.get(ptype, [])
        sampled.extend(group[:count])

    remaining = n - len(sampled)
    if remaining > 0:
        used_ids = {(p["catalog_id"], p["return_id"]) for p in sampled}
        extras = [p for p in pairs if (p["catalog_id"], p["return_id"]) not in used_ids]
        sampled.extend(extras[:remaining])

    return sampled


# ================================================================
# 3. API client
# ================================================================
async def health_check(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get("/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            logger.info(
                "Server healthy (gpu=%s, ollama=%s, cache=%d)",
                data.get("gpu_available"),
                data.get("ollama_connected"),
                data.get("cache_size", 0),
            )
            return True
        return False
    except httpx.ConnectError:
        return False


async def ingest_catalog(
    client: httpx.AsyncClient,
    product_id: str,
    image_path: Path,
) -> dict:
    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/png")}
        data = {"product_id": product_id}
        resp = await client.post(
            "/catalog",
            data=data,
            files=files,
            timeout=CATALOG_TIMEOUT,
        )
    resp.raise_for_status()
    return resp.json()


async def verify_return(
    client: httpx.AsyncClient,
    product_id: str,
    image_path: Path,
) -> dict:
    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/png")}
        data = {"product_id": product_id}
        t0 = time.perf_counter()
        resp = await client.post(
            "/verify",
            data=data,
            files=files,
            timeout=VERIFY_TIMEOUT,
        )
    elapsed = (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    result = resp.json()
    result["_client_latency_ms"] = round(elapsed, 1)
    return result


def image_path_for(product_id: str) -> Path:
    """Resolve fixture image path from product_id like 'saree_003'."""
    cat, idx = product_id.rsplit("_", 1)
    filename = f"{cat}_{int(idx):03d}.png"
    return FIXTURES_DIR / "images" / filename


# ================================================================
# 4. Main eval pipeline
# ================================================================
async def run_eval(
    base_url: str,
    pairs: list[dict],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(base_url=base_url) as client:
        # -- Health check --
        if not await health_check(client):
            logger.error("Server not reachable at %s", base_url)
            logger.error("Start it: uv run uvicorn app.presentation.main:app --port 8000")
            sys.exit(1)

        # -- Phase 1: Ingest all unique catalog images --
        unique_products = list(
            {p["catalog_id"] for p in pairs} | {p["return_id"] for p in pairs}
        )

        logger.info("Phase 1: Ingesting %d catalog images...", len(unique_products))
        t_ingest_start = time.perf_counter()

        for i, pid in enumerate(unique_products, 1):
            img_path = image_path_for(pid)
            if not img_path.exists():
                logger.warning("  Image not found: %s", img_path)
                continue
            result = await ingest_catalog(client, pid, img_path)
            logger.info(
                "  [%d/%d] Ingested %s (%d dims)",
                i, len(unique_products), pid, result.get("embedding_dims", 0),
            )

        t_ingest = time.perf_counter() - t_ingest_start
        logger.info("Phase 1 done (%.1fs)", t_ingest)

        # -- Phase 2: Verify each pair --
        logger.info("Phase 2: Running %d verify calls...", len(pairs))
        results: list[dict] = []
        t_verify_start = time.perf_counter()

        for i, pair in enumerate(pairs, 1):
            return_path = image_path_for(pair["return_id"])
            if not return_path.exists():
                logger.warning("  [%d/%d] Image not found: %s", i, len(pairs), return_path)
                continue

            try:
                api_result = await verify_return(client, pair["catalog_id"], return_path)
            except httpx.TimeoutException:
                logger.warning("  [%d/%d] TIMEOUT: %s vs %s",
                             i, len(pairs), pair["catalog_id"], pair["return_id"])
                results.append({**pair, "decision": "TIMEOUT", "confidence": 0.0,
                              "client_latency_ms": 0, "error": "timeout"})
                continue
            except httpx.HTTPStatusError as exc:
                logger.warning("  [%d/%d] HTTP %d: %s vs %s",
                             i, len(pairs), exc.response.status_code,
                             pair["catalog_id"], pair["return_id"])
                results.append({**pair, "decision": "ERROR", "confidence": 0.0,
                              "client_latency_ms": 0, "error": str(exc)})
                continue

            actual = api_result["decision"]
            expected = pair["expected"]
            correct = actual == expected
            client_lat = api_result.pop("_client_latency_ms", 0)
            explanation = api_result.get("explanation", "")

            result = {
                **pair,
                "decision": actual,
                "confidence": api_result.get("confidence", 0.0),
                "server_latency_ms": api_result.get("latency_ms", 0),
                "client_latency_ms": client_lat,
                "explanation": explanation,
                "suspect_reason": api_result.get("suspect_reason"),
                "baseline_threshold": api_result.get("baseline_threshold"),
                "correct": correct,
                "has_gemma_explanation": bool(explanation),
            }
            results.append(result)

            gemma_tag = " [GEMMA]" if explanation else ""
            logger.info(
                "  [%d/%d] %s vs %s -> %s (exp:%s) conf=%.3f lat=%.0fms%s",
                i, len(pairs), pair["catalog_id"], pair["return_id"],
                actual, expected, result["confidence"], client_lat, gemma_tag,
            )

        t_verify = time.perf_counter() - t_verify_start

        # -- Phase 3: Metrics --
        logger.info("Phase 3: Computing metrics...")
        metrics = _compute_metrics(results)
        metrics["timing"] = {
            "ingest_s": round(t_ingest, 1),
            "verify_s": round(t_verify, 1),
            "total_s": round(t_ingest + t_verify, 1),
            "pairs_tested": len(results),
        }

        # -- Phase 4: Write outputs --
        _write_report(results, metrics, output_dir)
        _print_summary(results, metrics)


# ================================================================
# 5. Metrics
# ================================================================
def _compute_metrics(results: list[dict]) -> dict:
    valid = [r for r in results if r.get("decision") not in ("TIMEOUT", "ERROR")]
    if not valid:
        return {}

    tp = sum(1 for r in valid if r["correct"] and r["expected"] == "MATCH")
    tn = sum(1 for r in valid if r["correct"] and r["expected"] == "REJECT")
    fp = sum(1 for r in valid if not r["correct"] and r["decision"] == "MATCH")
    fn = sum(1 for r in valid if not r["correct"] and r["decision"] == "REJECT")

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    gemma_calls = sum(1 for r in valid if r.get("has_gemma_explanation"))
    avg_latency = sum(r["client_latency_ms"] for r in valid) / len(valid)

    by_type: dict[str, dict] = {}
    for r in valid:
        pt = r["pair_type"]
        by_type.setdefault(pt, {"total": 0, "correct": 0, "gemma": 0})
        by_type[pt]["total"] += 1
        by_type[pt]["correct"] += int(r["correct"])
        by_type[pt]["gemma"] += int(r.get("has_gemma_explanation", False))

    wrong = [r for r in valid if not r["correct"]]

    return {
        "total_pairs": len(results),
        "valid_pairs": len(valid),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "gemma_calls": gemma_calls,
        "avg_latency_ms": round(avg_latency, 1),
        "by_type": by_type,
        "wrong_predictions": [
            {
                "pair": f"{r['catalog_id']} vs {r['return_id']}",
                "expected": r["expected"],
                "actual": r["decision"],
                "confidence": r["confidence"],
                "type": r["pair_type"],
            }
            for r in wrong
        ],
    }


# ================================================================
# 6. Output
# ================================================================
def _write_report(results: list[dict], metrics: dict, output_dir: Path) -> None:
    with open(output_dir / "e2e_results.json", "w") as f:
        json.dump({"metrics": metrics, "results": results}, f, indent=2, default=str)

    lines = [
        "# VerifAI E2E API Evaluation Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Pairs tested: {metrics.get('total_pairs', 0)}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Accuracy | **{metrics.get('accuracy', 0):.2%}** |",
        f"| Precision | {metrics.get('precision', 0):.2%} |",
        f"| Recall | {metrics.get('recall', 0):.2%} |",
        f"| F1 | {metrics.get('f1', 0):.2%} |",
        f"| Gemma calls | {metrics.get('gemma_calls', 0)} |",
        f"| Avg latency | {metrics.get('avg_latency_ms', 0):.0f}ms |",
        "",
        "## Timing",
        "",
        "| Phase | Time |",
        "|-------|------|",
    ]
    for k, v in metrics.get("timing", {}).items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    wrong = metrics.get("wrong_predictions", [])
    if wrong:
        lines.append("## Wrong Predictions")
        lines.append("")
        lines.append("| Pair | Expected | Actual | Confidence | Type |")
        lines.append("|------|----------|--------|------------|------|")
        for wp in wrong:
            lines.append(
                f"| {wp['pair']} | {wp['expected']} | {wp['actual']} | "
                f"{wp['confidence']:.4f} | {wp['type']} |"
            )
        lines.append("")

    by_type = metrics.get("by_type", {})
    if by_type:
        lines.append("## By Pair Type")
        lines.append("")
        lines.append("| Type | Total | Correct | Accuracy | Gemma calls |")
        lines.append("|------|-------|---------|----------|-------------|")
        for pt, stats in by_type.items():
            acc = stats["correct"] / stats["total"] if stats["total"] else 0
            lines.append(f"| {pt} | {stats['total']} | {stats['correct']} | {acc:.1%} | {stats['gemma']} |")
        lines.append("")

    with_expl = [r for r in results if r.get("explanation")]
    if with_expl:
        lines.append("## Gemma Explanations")
        lines.append("")
        for r in with_expl[:20]:
            lines.append(f"### {r['catalog_id']} vs {r['return_id']}")
            lines.append(f"- Decision: **{r['decision']}** (expected: {r['expected']})")
            lines.append(f"- Confidence: {r['confidence']:.4f}")
            lines.append(f"- Suspect reason: {r.get('suspect_reason', 'N/A')}")
            lines.append(f"- Explanation: {r['explanation']}")
            lines.append("")

    with open(output_dir / "e2e_report.md", "w") as f:
        f.write("\n".join(lines))

    logger.info("Results written to %s", output_dir)


def _print_summary(results: list[dict], metrics: dict) -> None:
    w = 72
    timing = metrics.get("timing", {})
    print(f"\n{'=' * w}")
    print(f"  VerifAI E2E API Evaluation Summary")
    print(f"{'=' * w}")
    print(f"\n  Pairs tested:   {metrics.get('valid_pairs', 0)} / {metrics.get('total_pairs', 0)}")
    print(f"  Accuracy:       {metrics.get('accuracy', 0):.2%}")
    print(f"  Precision:      {metrics.get('precision', 0):.2%}")
    print(f"  Recall:         {metrics.get('recall', 0):.2%}")
    print(f"  F1:             {metrics.get('f1', 0):.2%}")
    print(f"  Gemma calls:    {metrics.get('gemma_calls', 0)}")
    print(f"  Avg latency:    {metrics.get('avg_latency_ms', 0):.0f}ms")
    print(f"\n  Timing:")
    print(f"    Ingest:   {timing.get('ingest_s', 0):.1f}s")
    print(f"    Verify:   {timing.get('verify_s', 0):.1f}s")
    print(f"    Total:    {timing.get('total_s', 0):.1f}s")

    print(f"\n  {'Confusion Matrix':^40}")
    print(f"  {'-' * 40}")
    print(f"  TP: {metrics.get('tp', 0):>5}   FP: {metrics.get('fp', 0):>5}")
    print(f"  FN: {metrics.get('fn', 0):>5}   TN: {metrics.get('tn', 0):>5}")

    wrong = metrics.get("wrong_predictions", [])
    if wrong:
        print(f"\n  Wrong predictions ({len(wrong)}):")
        for wp in wrong:
            print(f"    {wp['pair']:30s} exp={wp['expected']:6s} got={wp['actual']:6s} "
                  f"conf={wp['confidence']:.3f} [{wp['type']}]")
    else:
        print(f"\n  No wrong predictions!")

    print(f"\n  Output:")
    print(f"    {OUTPUT_DIR / 'e2e_results.json'}")
    print(f"    {OUTPUT_DIR / 'e2e_report.md'}")
    print(f"{'=' * w}\n")


# ================================================================
# CLI
# ================================================================
def main() -> None:
    parser = argparse.ArgumentParser(description="VerifAI E2E API Evaluation")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--full", action="store_true", help="Test all 820 pairs")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument(
        "--pair-types",
        nargs="+",
        choices=["genuine", "same_category", "cross_category"],
        default=["genuine", "same_category", "cross_category"],
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["saree", "kurta", "sherwani", "lehenga"],
        default=None,
    )
    args = parser.parse_args()

    manifest = load_manifest()
    if args.categories:
        manifest = [m for m in manifest if m["category"] in args.categories]

    pairs = generate_pairs(manifest)
    pairs = [p for p in pairs if p["pair_type"] in args.pair_types]

    if not args.full:
        pairs = stratified_sample(pairs, args.sample_size)

    logger.info("Running %d pairs (types: %s)", len(pairs, args.pair_types))

    asyncio.run(run_eval(args.base_url, pairs, OUTPUT_DIR))


if __name__ == "__main__":
    main()
