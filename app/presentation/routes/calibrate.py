from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter

from app.presentation.schemas import (
    CalibrateRequest,
    CalibrateResponse,
    CalibrationStatsResponse,
)

router = APIRouter(tags=["calibration"])

CALIBRATION_PATH_ENV = "CALIBRATION_PATH"
DEFAULT_CALIBRATION_PATH = "data/calibration.jsonl"


def _cal_path() -> Path:
    return Path(os.environ.get(CALIBRATION_PATH_ENV, DEFAULT_CALIBRATION_PATH))


@router.post("/calibrate", response_model=CalibrateResponse)
async def post_calibrate(req: CalibrateRequest) -> CalibrateResponse:
    path = _cal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = req.model_dump()
    entry["cosine_sim"] = float(entry["cosine_sim"])
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return CalibrateResponse(status="recorded")


@router.get("/calibration/stats", response_model=CalibrationStatsResponse)
async def get_calibration_stats() -> CalibrationStatsResponse:
    path = _cal_path()
    if not path.exists():
        return CalibrationStatsResponse(status="no_data")

    categories: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "false_flag": 0, "false_pass": 0},
    )
    with open(path) as f:
        for line in f:
            entry = json.loads(line.strip())
            cat = entry["category"]
            decision = entry["decision"]
            human_label = entry["human_label"]
            categories[cat]["total"] += 1

            if decision in ("SUSPECT", "REJECT") and human_label == "genuine":
                categories[cat]["false_flag"] += 1
            elif decision == "MATCH" and human_label == "counterfeit":
                categories[cat]["false_pass"] += 1

    result = {}
    for cat, stats in categories.items():
        total = stats["total"]
        result[cat] = {
            "type1_rate": round(stats["false_flag"] / total, 4) if total else 0.0,
            "type2_rate": round(stats["false_pass"] / total, 4) if total else 0.0,
            "total": total,
        }
    return CalibrationStatsResponse(categories=result)
