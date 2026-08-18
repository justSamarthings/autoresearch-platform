"""
Register a Phase 2 training result JSON with the FastAPI backend.

Training stays decoupled from the database: this script only POSTs the artifact.

Usage (API must be reachable from this machine):
  python scripts/register_experiment.py tests/fixtures/exp_20260818_091852.json
  python scripts/register_experiment.py --latest
  python scripts/register_experiment.py --latest --verify

Environment:
  AUTORESEARCH_API_URL  Base URL of the API (default http://127.0.0.1:8000)

Colab: set AUTORESEARCH_API_URL to a tunnel/public URL that reaches your FastAPI
process (localhost on your laptop is not reachable from Colab without a tunnel).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_API_URL = "http://127.0.0.1:8000"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "training" / "artifacts" / "results"


def api_base_url(cli_value: str | None = None) -> str:
    if cli_value:
        return cli_value.rstrip("/")
    return os.environ.get("AUTORESEARCH_API_URL", DEFAULT_API_URL).rstrip("/")


def latest_result_json(results_dir: Path | None = None) -> Path:
    directory = results_dir if results_dir is not None else RESULTS_DIR
    files = sorted(directory.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No result JSON files under {directory}")
    return files[-1]


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            parsed = json.loads(body) if body else None
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body) if err_body else {"detail": err_body}
        except json.JSONDecodeError:
            parsed = {"detail": err_body}
        return e.code, parsed


def check_health(base_url: str) -> dict[str, Any]:
    status, body = _request_json("GET", f"{base_url}/health")
    if status != 200:
        raise RuntimeError(f"Health check failed ({status}): {body}")
    return body if isinstance(body, dict) else {"status": body}


def register_result(
    result: dict[str, Any],
    base_url: str,
) -> dict[str, Any]:
    if "experiment_id" not in result:
        raise ValueError("result JSON missing experiment_id")
    status, body = _request_json("POST", f"{base_url}/api/v1/experiments", payload=result)
    if status != 200:
        raise RuntimeError(f"Register failed ({status}): {body}")
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected register response: {body}")
    return body


def fetch_experiment(base_url: str, experiment_id: str) -> dict[str, Any]:
    status, body = _request_json("GET", f"{base_url}/api/v1/experiments/{experiment_id}")
    if status != 200:
        raise RuntimeError(f"Fetch experiment failed ({status}): {body}")
    if not isinstance(body, dict):
        raise RuntimeError(f"Unexpected experiment response: {body}")
    return body


def verify_registration(result: dict[str, Any], registered: dict[str, Any], base_url: str) -> dict[str, Any]:
    experiment_id = result["experiment_id"]
    detail = fetch_experiment(base_url, experiment_id)
    if detail.get("experiment_id") != experiment_id:
        raise RuntimeError("Verified experiment_id mismatch")
    if result.get("val_bpb") is not None and detail.get("val_bpb") != result.get("val_bpb"):
        raise RuntimeError(
            f"val_bpb mismatch: result={result.get('val_bpb')} api={detail.get('val_bpb')}"
        )
    if result.get("git_commit") and detail.get("git_commit") != result.get("git_commit"):
        raise RuntimeError("git_commit mismatch after registration")
    if not detail.get("checkpoints") and result.get("checkpoint_path"):
        raise RuntimeError("expected checkpoint metadata on registered experiment")
    return detail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register AutoResearch result JSON with FastAPI")
    parser.add_argument(
        "result_json",
        nargs="?",
        type=Path,
        help="Path to Phase 2 result JSON (omit with --latest)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help=f"Use newest JSON under {RESULTS_DIR}",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL (default: AUTORESEARCH_API_URL or http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="GET the experiment after POST and check key fields",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip GET /health before registration",
    )
    args = parser.parse_args(argv)

    if args.latest:
        path = latest_result_json()
    elif args.result_json is not None:
        path = args.result_json
    else:
        parser.error("provide result_json or --latest")

    base = api_base_url(args.base_url)
    result = json.loads(path.read_text(encoding="utf-8"))

    print(f"API: {base}")
    print(f"Result: {path}")
    print(f"experiment_id: {result.get('experiment_id')}")

    if not args.skip_health:
        health = check_health(base)
        print(f"health: {health}")

    response = register_result(result, base)
    created = response.get("created")
    experiment = response.get("experiment") or {}
    print(f"registered: created={created} val_bpb={experiment.get('val_bpb')}")

    if args.verify:
        detail = verify_registration(result, response, base)
        print(
            "verify OK:",
            detail.get("experiment_id"),
            "metrics=",
            len(detail.get("metrics") or []),
            "checkpoints=",
            len(detail.get("checkpoints") or []),
        )

    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
