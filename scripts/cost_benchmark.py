"""Compare baseline vs cost_spike metrics."""
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")
REPORT = Path("data/cost_comparison.json")


def get_metrics() -> dict:
    r = httpx.get(f"{BASE}/metrics", timeout=5)
    return r.json()


def send_requests(concurrency: int = 3) -> None:
    lines = [l for l in QUERIES.read_text().splitlines() if l.strip()]
    total = 0
    errors = 0
    with httpx.Client(timeout=15) as client:
        for line in lines:
            try:
                r = client.post(f"{BASE}/chat", json=json.loads(line))
                if r.status_code == 200:
                    total += 1
                else:
                    errors += 1
            except Exception:
                errors += 1
    print(f"  Sent {len(lines)} requests: {total} ok, {errors} errors")


def main() -> None:
    subprocess.run(["rm", "-f", "data/logs.jsonl", "data/audit.jsonl"])

    # Wait for app health
    for _ in range(10):
        try:
            r = httpx.get(f"{BASE}/health", timeout=3)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(1)

    # --- BASELINE ---
    print("\n=== BASELINE (no incident) ===")
    httpx.post(f"{BASE}/incidents/cost_spike/disable", timeout=5)
    time.sleep(0.5)
    before = get_metrics()
    send_requests()
    baseline = get_metrics()
    baseline_avg = baseline["avg_cost_usd"]
    baseline_total = baseline["total_cost_usd"]
    baseline_tokens = baseline["tokens_out_total"]
    print(f"  Avg cost/req: ${baseline_avg:.6f}")
    print(f"  Total cost: ${baseline_total:.4f}")
    print(f"  Tokens out: {baseline_tokens}")

    # --- COST SPIKE ---
    print("\n=== COST SPIKE (enabled) ===")
    httpx.post(f"{BASE}/incidents/cost_spike/enable", timeout=5)
    time.sleep(0.5)
    send_requests()
    spike = get_metrics()
    spike_avg = spike["avg_cost_usd"]
    spike_total = spike["total_cost_usd"]
    spike_tokens = spike["tokens_out_total"]
    print(f"  Avg cost/req: ${spike_avg:.6f}")
    print(f"  Total cost: ${spike_total:.4f}")
    print(f"  Tokens out: {spike_tokens}")

    # --- DISABLE BACK ---
    httpx.post(f"{BASE}/incidents/cost_spike/disable", timeout=5)

    # --- COMPARISON ---
    # Calculate the cost per request for baseline-only and spike-only
    # Since metrics are cumulative, we subtract baseline from spike to get spike-only contribution
    spike_only_cost = spike_total - baseline_total
    spike_only_reqs = spike["traffic"] - baseline["traffic"]
    spike_only_tokens = spike_tokens - baseline_tokens
    spike_only_avg = spike_only_cost / spike_only_reqs if spike_only_reqs else 0

    baseline_only_reqs = baseline["traffic"]
    baseline_only_cost = baseline_total
    baseline_only_avg = baseline_only_cost / baseline_only_reqs if baseline_only_reqs else 0

    multiplier = spike_only_avg / baseline_only_avg if baseline_only_avg else 0

    result = {
        "baseline": {"requests": baseline_only_reqs, "avg_cost_usd": round(baseline_only_avg, 6), "total_cost_usd": round(baseline_only_cost, 6), "tokens_out": baseline_tokens},
        "cost_spike": {"requests": spike_only_reqs, "avg_cost_usd": round(spike_only_avg, 6), "total_cost_usd": round(spike_only_cost, 6), "tokens_out": spike_only_tokens},
        "multiplier": round(multiplier, 2),
    }
    REPORT.write_text(json.dumps(result, indent=2))
    print(f"\n=== COMPARISON ===")
    print(f"  Baseline avg cost/req: ${baseline_only_avg:.6f}")
    print(f"  Cost-spike avg cost/req: ${spike_only_avg:.6f}")
    print(f"  Cost multiplier: {multiplier:.2f}x")
    print(f"  Report saved to {REPORT}")


if __name__ == "__main__":
    main()
