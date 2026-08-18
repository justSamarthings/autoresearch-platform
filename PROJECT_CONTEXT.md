# PROJECT_CONTEXT.md

Living project context for **AutoResearch Experiment Platform**.
Maintain this file only — do not add parallel status/architecture docs.

---

## 1. Project purpose

Personal open-source ML engineering platform for experiment tracking, evaluation, inference, and observability around Karpathy’s AutoResearch research loop.

## 2. Current architecture

```
Google Colab GPU
  └── training/ → artifacts/results/*.json (+ checkpoints/*.pt on disk)
        ↓
scripts/register_experiment.py  (AUTORESEARCH_API_URL)
        ↓
FastAPI  POST /api/v1/experiments
        ↓
Supabase PostgreSQL
        ↓
GET /api/v1/experiments/{experiment_id}

Frontend — not started
```

Training does **not** import Supabase/FastAPI. Registration is a separate post-train step.

## 3. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js scaffold only |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Database | PostgreSQL (Supabase) |
| Training | TinyStories AutoResearch under `training/` |
| Registration | `scripts/register_experiment.py` + Colab notebook STEP 7 |

## 4. Repository structure

```
/
├── backend/                 # API + migrations
├── training/                # AutoResearch (do not couple to API)
├── scripts/
│   ├── colab_train.ipynb    # train smoke + register
│   ├── register_experiment.py
│   ├── ingest_result.py     # thin wrapper → register_experiment
│   └── verify_checkpoint.py
├── tests/
│   ├── test_api_experiments.py
│   ├── test_register_experiment.py
│   └── fixtures/exp_20260818_091852.json
└── PROJECT_CONTEXT.md
```

## 5. Database schema

Unchanged from Phase 3: `experiments`, `experiment_metrics`, `checkpoints`, plus reserved `evaluations` / `inference_runs`.

## 6. Important design decisions

- Colab cannot reach laptop `localhost` without a tunnel/public API URL.
- Registration uses the **same** Phase 2 result JSON; idempotent by `experiment_id`.
- Checkpoint **files** still not uploaded — path/metadata only.
- CORS `*` enabled on API for tunneled/browser clients.

## 7. Current implementation status

**Phase 4 registration path implemented** (script + Colab STEP 7 + tests).  
Phases 2–3 remain verified (Colab smoke + live Supabase ingest).

## 8. Completed tasks

- [x] Phases 0–3 (training foundation, API, Supabase migrate/ingest)
- [x] Phase 4: `register_experiment.py`, Colab register step, registration tests, CORS

## 9. Current task

None — waiting for next phase instructions (dashboard / Phase 5).

## 10. Known limitations

- End-to-end **Colab → tunnel → API → Supabase** still requires you to run FastAPI + a public tunnel and set `AUTORESEARCH_API_URL` in Colab (not runnable from this Windows agent alone).
- No auth on ingest yet (fine for personal MVP; harden before public deploy).
- FA3 still falls back to SDPA on Colab.
- Rotate DB password if it was ever pasted into chat.

## 11. Next planned tasks

1. **Phase 5:** Next.js dashboard (overview + experiments list/detail).
2. Compare / research progress / models views.
3. Manual evaluation + inference UIs.
4. Optional: checkpoint file upload/storage.

## 12. Important commands

```bash
# Tests
backend/.venv/Scripts/python -m pytest tests -q

# API (repo root)
backend/.venv/Scripts/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Register local result (API must be up)
python scripts/register_experiment.py tests/fixtures/exp_20260818_091852.json --verify
python scripts/register_experiment.py --latest --verify

# Colab: set AUTORESEARCH_API_URL then run notebook through STEP 7
```

## 13. Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Supabase Postgres for API |
| `AUTORESEARCH_API_URL` | FastAPI base URL for registration (Colab/tunnel) |
| `AUTORESEARCH_TIME_BUDGET` / `NO_COMPILE` / `CACHE` / `EXPERIMENT_ID` | training |

## 14. API endpoints

Unchanged from Phase 3 (`/health`, `/api/v1/experiments*`, `/api/v1/checkpoints*`).

## 15. Decisions that should not be accidentally changed

- Training remains decoupled from Supabase/FastAPI.
- Do not store checkpoint binaries in Postgres.
- Primary metric remains `val_bpb`.
- Only `PROJECT_CONTEXT.md` as living context doc.
- Work in phases; stop after each phase.
