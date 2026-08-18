import json
from pathlib import Path

import pytest

from scripts import register_experiment as reg


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "exp_20260818_091852.json"


def test_api_base_url_env(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_API_URL", "https://example.test/api/")
    assert reg.api_base_url() == "https://example.test/api"
    assert reg.api_base_url("http://override:8000/") == "http://override:8000"


def test_latest_result_json(tmp_path):
    older = tmp_path / "exp_a.json"
    newer = tmp_path / "exp_b.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")
    assert reg.latest_result_json(tmp_path) == newer


def test_register_and_verify_against_api(client, sample_result, monkeypatch):
    """Integration: registration helpers against FastAPI TestClient transport."""

    def fake_request(method, url, payload=None, timeout=60.0):
        path = url.split("://", 1)[-1]
        # url is http://testserver/...
        path = "/" + path.split("/", 1)[-1] if "://" in url else url
        # TestClient expects path only
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json=payload)
        else:
            raise AssertionError(method)
        body = resp.json() if resp.content else None
        return resp.status_code, body

    monkeypatch.setattr(reg, "_request_json", fake_request)

    base = "http://testserver"
    health = reg.check_health(base)
    assert health["status"] == "ok"

    response = reg.register_result(sample_result, base)
    assert response["created"] is True
    assert response["experiment"]["experiment_id"] == sample_result["experiment_id"]

    again = reg.register_result(sample_result, base)
    assert again["created"] is False

    detail = reg.verify_registration(sample_result, response, base)
    assert detail["val_bpb"] == sample_result["val_bpb"]
    assert len(detail["checkpoints"]) == 1


def test_register_cli_latest(tmp_path, client, sample_result, monkeypatch):
    results = tmp_path / "results"
    results.mkdir()
    path = results / f"{sample_result['experiment_id']}.json"
    path.write_text(json.dumps(sample_result), encoding="utf-8")

    monkeypatch.setattr(reg, "RESULTS_DIR", results)

    def fake_request(method, url, payload=None, timeout=60.0):
        from urllib.parse import urlparse

        path_only = urlparse(url).path
        if method == "GET":
            resp = client.get(path_only)
        else:
            resp = client.post(path_only, json=payload)
        return resp.status_code, resp.json()

    monkeypatch.setattr(reg, "_request_json", fake_request)
    assert reg.main(["--latest", "--verify", "--base-url", "http://testserver"]) == 0
