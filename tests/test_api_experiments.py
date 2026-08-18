def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ingest_and_get_experiment(client, sample_result):
    create = client.post("/api/v1/experiments", json=sample_result)
    assert create.status_code == 200
    body = create.json()
    assert body["created"] is True
    assert body["experiment"]["experiment_id"] == "exp_20260818_091852"
    assert body["experiment"]["val_bpb"] == pytest_approx_val_bpb(sample_result["val_bpb"])
    assert body["experiment"]["git_commit"] == sample_result["git_commit"]
    assert len(body["experiment"]["metrics"]) >= 1
    assert len(body["experiment"]["checkpoints"]) == 1

    got = client.get("/api/v1/experiments/exp_20260818_091852")
    assert got.status_code == 200
    detail = got.json()
    assert detail["experiment_id"] == sample_result["experiment_id"]
    assert detail["val_bpb"] == pytest_approx_val_bpb(sample_result["val_bpb"])
    assert detail["configuration"]["max_seq_len"] == 256
    assert detail["checkpoints"][0]["checkpoint_path"] == sample_result["checkpoint_path"]


def test_list_experiments(client, sample_result):
    client.post("/api/v1/experiments", json=sample_result)
    resp = client.get("/api/v1/experiments")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["experiment_id"] == "exp_20260818_091852"

    filtered = client.get("/api/v1/experiments", params={"status": "ok"})
    assert filtered.json()["total"] == 1
    empty = client.get("/api/v1/experiments", params={"status": "crash"})
    assert empty.json()["total"] == 0


def test_metrics_endpoint(client, sample_result):
    client.post("/api/v1/experiments", json=sample_result)
    resp = client.get("/api/v1/experiments/exp_20260818_091852/metrics")
    assert resp.status_code == 200
    metrics = {m["metric_name"]: m["metric_value"] for m in resp.json()}
    assert "val_bpb" in metrics
    assert metrics["val_bpb"] == pytest_approx_val_bpb(sample_result["val_bpb"])
    assert "num_params" in metrics


def test_duplicate_ingest_is_idempotent(client, sample_result):
    first = client.post("/api/v1/experiments", json=sample_result)
    second = client.post("/api/v1/experiments", json=sample_result)
    assert first.status_code == 200 and first.json()["created"] is True
    assert second.status_code == 200 and second.json()["created"] is False
    assert first.json()["experiment"]["id"] == second.json()["experiment"]["id"]

    listing = client.get("/api/v1/experiments")
    assert listing.json()["total"] == 1


def test_invalid_payload(client):
    resp = client.post("/api/v1/experiments", json={"status": "ok"})
    assert resp.status_code == 422


def test_checkpoint_metadata_relationship(client, sample_result):
    client.post("/api/v1/experiments", json=sample_result)
    listing = client.get("/api/v1/checkpoints")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    checkpoint_id = listing.json()["items"][0]["id"]
    detail = client.get(f"/api/v1/checkpoints/{checkpoint_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["checkpoint_path"] == sample_result["checkpoint_path"]
    assert body["metadata"]["experiment_id"] == sample_result["experiment_id"]
    assert body["metadata"]["val_bpb"] == pytest_approx_val_bpb(sample_result["val_bpb"])


def test_missing_experiment(client):
    resp = client.get("/api/v1/experiments/does-not-exist")
    assert resp.status_code == 404


def pytest_approx_val_bpb(value: float) -> float:
    # exact float compare for stored JSON number
    return value
