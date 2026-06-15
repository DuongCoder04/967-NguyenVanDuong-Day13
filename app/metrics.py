from __future__ import annotations

import time
from collections import Counter
from statistics import mean

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []
HISTORY: list[dict] = []


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)
    HISTORY.append({
        "ts": time.time(),
        "traffic": TRAFFIC,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "quality_score": quality_score,
        "error_breakdown": dict(ERRORS),
    })


def record_error(error_type: str) -> None:
    ERRORS[error_type] += 1
    if HISTORY:
        HISTORY[-1]["error_breakdown"] = dict(ERRORS)



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }


def history() -> list[dict]:
    result = []
    for i in range(len(HISTORY)):
        slice_latencies = [h["latency_ms"] for h in HISTORY[: i + 1]]
        result.append({
            **HISTORY[i],
            "latency_p50": percentile(slice_latencies, 50),
            "latency_p95": percentile(slice_latencies, 95),
            "latency_p99": percentile(slice_latencies, 99),
        })
    return result
