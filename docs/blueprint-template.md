# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Solo-967
- [REPO_URL]: https://github.com/DuongCoder04/967-NguyenVanDuong-Day13.git
- [MEMBERS]:
  - Member A: Nguyen Van Duong | Role: All (Individual work)

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 12
- [PII_LEAKS_FOUND]: 0 (PII scrubbing active via `app/pii.py` with 6 patterns: email, phone_vn, cccd, credit_card, passport_vn, address_vn)

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: screenshots/correlation-id.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: screenshots/pii-redaction.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: screenshots/trace-waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: The `rag_retrieve` span shows the RAG pipeline fetching context; with `rag_slow` incident enabled, this span's duration jumps from ~50ms to ~5000ms due to an artificial `time.sleep()` in the retrieval code, directly explaining the P95 latency spike.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: screenshots/dashboard-6-panels.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---:|---:|
| Latency P95 | < 3000ms | 28d | 151ms |
| Error Rate | < 2% | 28d | 0% (baseline) / 25% (rag_slow+tool_fail) |
| Cost Budget | < $2.5/day | 1d | $0.0911 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: screenshots/alerts-firing.png
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#2-high-error-rate]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow + tool_fail
- [SYMPTOMS_OBSERVED]: Latency P95 increased from ~150ms to ~5000ms; 5 RuntimeError errors recorded in error_breakdown; `high_error_rate` alert fired (error_rate_pct = 25%); quality_score dropped toward 0.88.
- [ROOT_CAUSE_PROVED_BY]: Trace logs show `rag_slow=True` induced `time.sleep(5)` in retrieval; tool_fail incident injected random `RuntimeError` in tool execution. Correlation ID `req-...` linked all log lines from request to response.
- [FIX_ACTION]: Disabled both incidents via `POST /incidents/{name}/disable`; latency and error rate returned to normal immediately.
- [PREVENTIVE_MEASURE]: Added alert rules in `config/alert_rules.yaml` with SLO-based thresholds (latency_p95 > 3000ms P2, error_rate > 2% P1, cost > $0.005/req P2, quality < 0.85 P2). Runbook documented in `docs/alerts.md`. Cooldown mechanism prevents alert spam (60s between re-fires).

---

## 5. Individual Contributions & Evidence

### Nguyen Van Duong
- [TASKS_COMPLETED]: 
  1. Structured logging with structlog + JSON output (`app/logging_config.py`)
  2. PII detection and scrubbing (6 regex patterns + hash_user_id) (`app/pii.py`)
  3. Contextual log enrichment (user_id_hash, session_id, feature, model, env) (`app/main.py`)
  4. Langfuse v4 tracing integration (`app/tracing.py`, `app/agent.py`)
  5. Correlation ID middleware (`app/middleware.py`)
  6. Custom metrics generator with time-series history (`app/metrics.py`)
  7. 6-panel Chart.js dashboard with auto-refresh (`app/dashboard.py`)
  8. Alert evaluator with 4 SLO-based rules (`app/alerts.py`)
  9. Alert runbook (`docs/alerts.md`)
  10. SLO configuration (`config/slo.yaml`)
  11. Incident injection for testing (`app/incidents.py`)
  12. PII test suite (`tests/test_pii.py`)
  13. Audit logging to `data/audit.jsonl` (`app/audit.py`)
  14. Cost optimization benchmark (baseline vs cost_spike comparison)
- [EVIDENCE_LINK]: https://github.com/DuongCoder04/967-NguyenVanDuong-Day13/commit/cf925a5

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Implemented cost benchmark comparing baseline vs cost_spike incident. Baseline avg cost: $0.00182/req. With cost_spike: $0.00729/req (4.01x multiplier). Automated via `scripts/cost_benchmark.py`. Results saved to `data/cost_comparison.json`.
- [BONUS_AUDIT_LOGS]: Separate audit log module (`app/audit.py`) writes structured JSON lines to `data/audit.jsonl`. Logs all sensitive operations: incident enable/disable (with success/failure outcome) and PII-containing requests. Entries include ISO timestamp, action, actor, detail, and outcome fields.
- [BONUS_CUSTOM_METRIC]: Custom quality_score metric tracks per-request response quality. Collected in `metrics.py` HISTORY, displayed on dashboard panel 6 ("Quality Score" gauge), and used by the `quality_drop` alert rule (threshold < 0.85).
