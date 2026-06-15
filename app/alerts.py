from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yaml

from .logging_config import get_logger
from .metrics import snapshot

log = get_logger()
FIRED: dict[str, dict] = {}
RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "alert_rules.yaml"


def load_rules() -> list[dict]:
    text = RULES_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data.get("alerts", [])


def evaluate() -> list[dict]:
    metrics = snapshot()
    traffic = metrics["traffic"]
    if traffic == 0:
        return [{"alert": r["name"], "severity": r["severity"], "status": "insufficient_data"} for r in load_rules()]
    error_rate_pct = round(
        (sum(metrics["error_breakdown"].values()) / traffic * 100) if traffic > 0 else 0, 2
    )
    cost_per_request = round(metrics["avg_cost_usd"], 6)
    context = {
        "latency_p95_ms": metrics["latency_p95"],
        "error_rate_pct": error_rate_pct,
        "cost_per_request_usd": cost_per_request,
        "quality_score_avg": metrics["quality_avg"],
    }

    results = []
    for rule in load_rules():
        cond = rule["condition"]
        name = rule["name"]
        value = _resolve_condition(cond, context)
        firing = value is not None and value is True

        if firing:
            prev = FIRED.get(name)
            now = time.time()
            if not prev or now - prev["fired_at"] >= 60:
                FIRED[name] = {"fired_at": now, "rule": rule, "context": dict(context)}
                log.warning(
                    "alert_fired",
                    service="alerts",
                    payload={
                        "alert": name,
                        "severity": rule["severity"],
                        "condition": cond,
                        "context": context,
                    },
                )
            results.append({"alert": name, "severity": rule["severity"], "status": "firing", "context": context})
        else:
            results.append({"alert": name, "severity": rule["severity"], "status": "ok"})

    return results


def _resolve_condition(cond: str, ctx: dict) -> bool | None:
    for key, val in ctx.items():
        if key in cond:
            thresh = _extract_threshold(cond, key)
            if thresh is None:
                continue
            if ">" in cond:
                return val > thresh
            if "<" in cond:
                return val < thresh
    return None


def _extract_threshold(cond: str, key: str) -> float | None:
    import re

    for op in [">", "<", ">=", "<="]:
        if op in cond:
            pattern = rf"{re.escape(key)}\s*{op}\s*([\d.]+)"
            m = re.search(pattern, cond)
            if m:
                return float(m.group(1))
    return None


def status() -> dict[str, dict]:
    return dict(FIRED)
