from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


def record(action: str, actor: str, detail: dict[str, Any], outcome: str = "success") -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.time(),
        "iso_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": action,
        "actor": actor,
        "detail": detail,
        "outcome": outcome,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
