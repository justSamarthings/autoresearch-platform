"""
POST a Phase 2 result JSON to the local FastAPI ingestion endpoint.

Usage (from repo root, with API running):
  python scripts/ingest_result.py training/artifacts/results/exp_20260818_091852.json
  python scripts/ingest_result.py tests/fixtures/exp_20260818_091852.json
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest AutoResearch result JSON via FastAPI")
    parser.add_argument("result_json", type=Path, help="Path to Phase 2 result JSON")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="FastAPI base URL",
    )
    args = parser.parse_args()

    payload = json.loads(args.result_json.read_text(encoding="utf-8"))
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{args.base_url.rstrip('/')}/api/v1/experiments",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            print(body)
            return 0
    except urllib.error.HTTPError as e:
        print(e.read().decode("utf-8"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
