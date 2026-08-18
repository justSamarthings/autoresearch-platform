# PROJECT_CONTEXT.md

Living project context for **AutoResearch Experiment Platform**.
Maintain this file only — do not add parallel status/architecture docs.
Owner/developer: project author (do not attribute authorship to AI/Cursor).

---

## 1. Project purpose

Personal open-source ML engineering platform around Karpathy AutoResearch:

`program.md` → agent edits `train.py` → fixed-time train → `val_bpb` → keep/discard → repeat

MVP pillars: **automated experimentation**, **evaluation**, **inference**, with visible research lineage (git → code change → metrics → checkpoint → eval/inference).

Not an MLflow clone. Not distributed training.

## 2. Current architecture

```
Google Colab (GPU worker)
  └── training/  → artifacts/results/*.json + checkpoints/*.pt
        ↓
scripts/register_experiment.py   (AUTORESEARCH_API_URL / tunnel)
        ↓
FastAPI (backend/)  POST/GET /api/v1/experiments*
        ↓
Supabase PostgreSQL
        ↓
Next.js dashboard (frontend/)  NEXT_PUBLIC_API_URL → localhost:3000
```

**Separation:** training never imports Supabase/FastAPI. Dashboard is read-only against GET APIs. Checkpoint **files** stay on disk (path/metadata in DB only).

## 3. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15 App Router, React 19, TypeScript, Tailwind |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2, Alembic |
| Database | PostgreSQL via Supabase |
| Training | PyTorch/CUDA, TinyStories, AutoResearch-style GPT under `training/` |

Out of scope for MVP: NeMo, Megatron, Ray, LangChain/LangGraph, MLflow, ClickHouse, Kafka, Redis, K8s.

## 4. Repository structure

```
/
├── frontend/          # Phase 5 dashboard
├── backend/           # Phase 3 API + Alembic
├── training/          # Phase 2 AutoResearch (TinyStories)
├── scripts/           # Colab notebook, register/verify helpers
├── tests/             # API + registration + training config tests
├── alembic.ini
└── PROJECT_CONTEXT.md
```

## 5. Database schema (Phase 3)

- **experiments** — unique `experiment_id`, status, git, val_bpb, config JSONB, checkpoint_path, …
- **experiment_metrics** — FK → experiments; name/value/step
- **checkpoints** — FK → experiments; path + metadata JSONB (no weights)
- **evaluations** / **inference_runs** — tables reserved; no workflows yet

## 6. Important design decisions

- Own git root (not a Karpathy fork); training vendored under `training/`.
- TinyStories + Colab small-compute (not ClimbMix).
- Primary metric: **val_bpb** (lower is better).
- Idempotent experiment ingest by `experiment_id`.
- Colab cannot hit laptop localhost without a tunnel/public API URL.
- Port **8000** must run **this** FastAPI (not other projects e.g. GXAssistant).
- Port **3000** runs this Next.js dashboard.

## 7. Current implementation status

**Phases 0–5 complete.**

Verified end-to-end pieces:

| Stage | Status |
|-------|--------|
| Colab 30s smoke train | PASS (`exp_20260818_091852`, val_bpb ≈ 0.827788) |
| Checkpoint reload | PASS |
| Supabase migrate + ingest | PASS (live) |
| Registration script/tests | PASS |
| Phase 4 Colab→API integration | PASS (user-verified) |
| Dashboard + production build | PASS (`next build`); UI reads live API |

## 8. Completed tasks / commits

- [x] Phase 1 scaffold — `9192510`
- [x] Phase 2 training foundation — `5cbf075`
- [x] Phase 3 backend + DB — `194e503`
- [x] Phase 4 registration path — `a70aceb`
- [x] Phase 5 Next.js overview / experiments / detail (this commit)

## 9. Current task

None active after Phase 5 commit. **Next: Phase 6** when instructed.

## 10. Known limitations

- No auth on API/UI (personal MVP only).
- No experiment compare / research-progress charts yet.
- No models browser polish beyond detail checkpoint metadata.
- No manual evaluation or inference UI/API workflows yet.
- FA3 on Colab often unavailable → SDPA + `WINDOW_PATTERN="L"`.
- Rotate Supabase DB password if it was ever pasted into chat; keep secrets only in gitignored `.env`.
- If dashboard shows API unhealthy: ensure AutoResearch uvicorn is on `:8000` (another app may steal the port).

## 11. Next planned tasks (direction)

**Phase 6 — Observability / research views**
1. Experiment comparison (multi-select: config, val_bpb, duration, throughput/status)
2. Research progress visualization (experiment lineage vs val_bpb)
3. Models / checkpoints list view (which experiment produced which checkpoint)

**Phase 7 — Evaluation + inference (product)**
1. Manual evaluation against a selected checkpoint (store in `evaluations`)
2. Inference UI (prompt → generate TinyStories text → store in `inference_runs`)
3. Optional checkpoint file upload/storage (still not Postgres blobs)

**Later**
- Auth / harden public deploy
- Deeper git diff display on experiment detail
- Keep/discard agent status sync beyond raw `status` field

## 12. Important commands

```bash
# Backend API (repo root)
backend/.venv/Scripts/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend
cd frontend
npm install
npm run dev -- -p 3000          # or: npx next dev -p 3000

# Register a result JSON
python scripts/register_experiment.py tests/fixtures/exp_20260818_091852.json --verify
python scripts/register_experiment.py --latest --verify

# Tests / checks
backend/.venv/Scripts/python -m pytest tests -q
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

## 13. Environment variables

| Variable | Where | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | `backend/.env` | Supabase Postgres (never commit) |
| `AUTORESEARCH_API_URL` | Colab / shell | FastAPI base for registration |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Dashboard → API (default `http://127.0.0.1:8000`) |
| `AUTORESEARCH_TIME_BUDGET` / `NO_COMPILE` / `CACHE` / `EXPERIMENT_ID` | training | Colab/smoke knobs |

## 14. API + UI map

| Method | Path | Used by |
|--------|------|---------|
| GET | `/health` | Dashboard health |
| POST | `/api/v1/experiments` | Registration |
| GET | `/api/v1/experiments` | Overview + list |
| GET | `/api/v1/experiments/{id}` | Detail |
| GET | `/api/v1/experiments/{id}/metrics` | Detail / metrics |
| GET | `/api/v1/checkpoints*` | Metadata only |

| UI route | Purpose |
|----------|---------|
| `/` | Overview stats + best model |
| `/experiments` | Table + status filter |
| `/experiments/[experimentId]` | Full experiment detail |

## 15. Training defaults (Phase 2)

`MAX_SEQ_LEN=256`, `VOCAB_SIZE=1024`, `TIME_BUDGET=300`, `EVAL_TOKENS=65536`, `DEPTH=4`, `WINDOW_PATTERN="L"`, `DEVICE_BATCH_SIZE=32`, `TOTAL_BATCH_SIZE=16384`.

## 16. Decisions that should not be accidentally changed

- Do not claim AI/Cursor authorship anywhere.
- Do not fork Karpathy as this repo root; keep training under `training/`.
- Do not store checkpoint binaries in Postgres.
- Do not replace `val_bpb` as primary metric.
- Do not add MLflow / heavy infra in MVP.
- Only maintain **PROJECT_CONTEXT.md** as the living context doc.
- Work in phases; stop after each phase until instructed.
