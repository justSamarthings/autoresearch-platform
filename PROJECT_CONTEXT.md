# PROJECT_CONTEXT.md

Living project context for **AutoResearch Experiment Platform**.
Maintain this file only — do not add parallel status/architecture docs.

---

## 1. Project purpose

Personal open-source ML engineering platform for experiment tracking, evaluation, inference, and observability around Karpathy’s AutoResearch research loop:

`program.md` → agent edits `train.py` → fixed-time train → `val_bpb` → keep/discard → repeat.

MVP capabilities: automated experimentation, model evaluation, model inference — with visible experiment lineage (git commit → code change → metrics → checkpoint → eval/inference).

## 2. Current architecture

```
Google Colab GPU
  └── training/ → artifacts/results/*.json + checkpoints/*.pt
        ↓
FastAPI (backend/)  POST /api/v1/experiments
        ↓
PostgreSQL (Supabase) — experiment / metrics / checkpoint metadata
        ↓
GET /api/v1/experiments/{experiment_id}

Frontend (Next.js) — not started
```

Training does **not** depend on Supabase. Checkpoint **files** stay outside the DB (path/reference only).

## 3. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js / React / TS (scaffold only) |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic |
| Database | PostgreSQL via Supabase (`DATABASE_URL`) |
| Training | PyTorch / CUDA, TinyStories AutoResearch under `training/` |

## 4. Repository structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/          # health, experiments, checkpoints
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── db/
│   ├── alembic/versions/001_initial_schema.py
│   ├── requirements.txt
│   └── .env.example
├── training/             # Phase 2 (unchanged this phase)
├── scripts/
│   ├── colab_train.ipynb
│   ├── ingest_result.py
│   └── verify_checkpoint.py
├── tests/
│   ├── fixtures/exp_20260818_091852.json
│   ├── test_api_experiments.py
│   └── test_training_config.py
├── alembic.ini
└── PROJECT_CONTEXT.md
```

## 5. Database schema

Tables (Alembic `001_initial`):

- **experiments** — unique `experiment_id`, status, git_commit/dirty, parent_experiment_id, timestamps, duration_seconds, val_bpb, num_params, depth, vocab_size, max_seq_len, window_pattern, checkpoint_path, configuration JSONB, crash_message
- **experiment_metrics** — FK → experiments.id; metric_name/value/step/recorded_at; unique (experiment_uuid, metric_name, step)
- **checkpoints** — FK → experiments.id; checkpoint_path + metadata JSONB (no binary weights)
- **evaluations** — schema only (Phase 7); FK → checkpoints / experiments
- **inference_runs** — schema only (Phase 7); FK → checkpoints

## 6. Important design decisions

- Ingest the **same** Phase 2 result JSON shape (no second format).
- Idempotent POST: duplicate `experiment_id` returns existing row (`created=false`).
- Store summary metrics from the result (`val_bpb`, timings, tokens, …) in `experiment_metrics`.
- Checkpoint binaries never uploaded in Phase 3.
- API tests use isolated SQLite `create_all`, not production Supabase.

## 7. Current implementation status

**Phase 3 backend/data foundation implemented.** API tests pass against SQLite. **Live Supabase verified:** Alembic `001_initial` applied; ingested `exp_20260818_091852` (idempotent re-POST); GET experiment/metrics/checkpoint metadata succeeded.

## 8. Completed tasks

- [x] Phases 0–2 + Colab smoke (`exp_20260818_091852`, val_bpb≈0.827788)
- [x] Phase 3: schema, Alembic, FastAPI ingest/list/get/metrics/checkpoints, tests, `.env.example`, `scripts/ingest_result.py`

## 9. Current task

None — waiting for Phase 4 (or Supabase manual wiring).

## 10. Known limitations

- Live Supabase session-pooler connection verified for migrate + ingest; keep secrets only in gitignored `backend/.env` (never commit). **Rotate DB password if it was shared in chat.**
- `evaluations` / `inference_runs` tables exist but have no APIs yet.
- FA3 kernels still fall back to SDPA on Colab.
- Hardened Colab notebook may still be uncommitted locally.
- Test fixture mirrors Phase 2 schema; confirmed Colab fields include experiment_id, git_commit, val_bpb, num_params, depth/config — prefer POSTing the real Colab JSON when available.

## 11. Next planned tasks (Phase 4+)

1. Wire Colab → POST result JSON to API (registration path).
2. Confirm live Supabase rows for real experiments.
3. Dashboard / compare / eval / inference UIs.

## 12. Important commands

```bash
# Backend deps
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt   # Windows
# source backend/.venv/bin/activate && pip install -r backend/requirements.txt  # Unix

# Tests (SQLite, no Supabase required)
backend/.venv/Scripts/python -m pytest tests/test_api_experiments.py tests/test_training_config.py -q

# Run API (from repo root)
# copy backend/.env.example → backend/.env and set DATABASE_URL
backend/.venv/Scripts/alembic upgrade head
backend/.venv/Scripts/uvicorn backend.app.main:app --reload --app-dir .

# Ingest a result JSON
python scripts/ingest_result.py tests/fixtures/exp_20260818_091852.json
# or: python scripts/ingest_result.py path/to/exp_20260818_091852.json
```

### Manual Supabase verification

1. Create Supabase project; copy Postgres URI into `backend/.env` as `DATABASE_URL=postgresql+psycopg://...`
2. `alembic upgrade head`
3. Start uvicorn
4. `POST` real Phase 2 JSON (e.g. Colab `exp_20260818_091852`)
5. `GET /api/v1/experiments/exp_20260818_091852` and `/metrics`
6. Confirm rows in Supabase Table Editor (`experiments`, `experiment_metrics`, `checkpoints`)
7. POST the same JSON again → `created: false`, still one row

## 13. Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL for Supabase Postgres (`postgresql+psycopg://...`) |
| Training vars | unchanged (`AUTORESEARCH_*`) |

## 14. API endpoints (Phase 3)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| POST | `/api/v1/experiments` | Ingest Phase 2 result JSON (idempotent) |
| GET | `/api/v1/experiments` | List (`limit`, `offset`, `status`) |
| GET | `/api/v1/experiments/{experiment_id}` | Detail + metrics + checkpoint metadata |
| GET | `/api/v1/experiments/{experiment_id}/metrics` | Metrics only |
| GET | `/api/v1/checkpoints` | Checkpoint metadata list |
| GET | `/api/v1/checkpoints/{checkpoint_id}` | Checkpoint metadata detail |

## 15. Training configuration

Unchanged from Phase 2 (TinyStories small-compute defaults). Do not modify `training/prepare.py` / `train.py` casually.

## 16. Decisions that should not be accidentally changed

- Do not claim AI/Cursor authorship.
- Training remains decoupled from Supabase.
- Do not store checkpoint binaries in Postgres.
- Do not replace `val_bpb` as primary metric.
- Do not add MLflow / heavy infra in MVP.
- Only `PROJECT_CONTEXT.md` as living context doc.
- Work in phases; stop after each phase.
