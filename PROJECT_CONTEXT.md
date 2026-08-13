# PROJECT_CONTEXT.md

Living project context for **AutoResearch Experiment Platform**.
Maintain this file only — do not add parallel status/architecture docs.

---

## 1. Project purpose

Personal open-source ML engineering platform for experiment tracking, evaluation, inference, and observability around Karpathy’s AutoResearch research loop:

`program.md` → agent edits `train.py` → fixed-time train → `val_bpb` → keep/discard → repeat.

MVP capabilities: automated experimentation, model evaluation, model inference — with visible experiment lineage (git commit → code change → metrics → checkpoint → eval/inference).

Not an MLflow clone. Not a distributed training system.

## 2. Current architecture

```
Local / deployed app (no GPU assumed)
  └── FastAPI + Postgres (Supabase)     [not implemented yet]
        ↑ register metrics / checkpoints / eval / inference
Google Colab (GPU worker)
  └── training/ (AutoResearch)          [not implemented yet]
```

GPU execution is decoupled from the web app. Single-GPU only for MVP.

## 3. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js, React, TypeScript (planned) |
| Backend | Python, FastAPI (planned) |
| Database | PostgreSQL via Supabase (planned) |
| Training | PyTorch / CUDA, AutoResearch-style GPT on TinyStories (Phase 2) |

Out of scope for MVP: NeMo, Megatron, Ray, LangChain, LangGraph, MLflow, ClickHouse, Kafka, Redis, Kubernetes.

## 4. Repository structure

```
/
├── frontend/          # Next.js UI (empty scaffold)
├── backend/           # FastAPI + DB access (empty scaffold)
├── training/          # AutoResearch training integration (empty scaffold)
├── scripts/           # Setup / import / Colab helpers (empty scaffold)
├── tests/             # Backend / training tests (empty scaffold)
├── .gitignore
└── PROJECT_CONTEXT.md
```

Training lives under `training/` as a near-copy of upstream roles (`prepare.py`, `train.py`, `program.md`). No git submodule. This repo is **not** a fork of karpathy/autoresearch.

## 5. Database schema

Not implemented. Planned tables (MVP):

- `experiments` — id, name/number, status, timestamps, duration, git_commit, parent_experiment_id, checkpoint ref, val_bpb, configuration (JSONB), notes
- `experiment_metrics` — experiment_id, metric_name, metric_value, step, timestamp
- `checkpoints` — id, experiment_id, path/reference, created_at, metadata
- `evaluations` — id, checkpoint_id, dataset, config, metrics, timestamps
- `inference_runs` — id, checkpoint_id, prompt, output, generation params, timestamp

Primary metric: **val_bpb** (lower is better). Secondary metrics only if training actually produces them.

## 6. Important design decisions

- New git repo owned by the project developer — not a Karpathy fork/clone as the project root.
- Platform wraps AutoResearch; does not replace the training core.
- `prepare.py` remains the fixed data/eval/utilities surface; `train.py` is the agent-editable surface; `program.md` is human-edited agent context.
- TinyStories + Colab-scale knobs in **one** Phase 2 change set (no ClimbMix-first then redo).
- App server must not assume a local GPU.
- Do not invent metrics, features, or authors (no AI/Cursor authorship in docs/UI/metadata).
- Single living context file: this file only.

## 7. Current implementation status

**Phase 1 complete.** Scaffold + git + context only.

## 8. Completed tasks

- [x] Task 0: Inspect empty workspace and upstream karpathy/autoresearch
- [x] Phase 1: `git init` (branch `main`), directory scaffold, `.gitignore`, `PROJECT_CONTEXT.md`
- [x] Phase 1 structure checks passed (required dirs/files present; no unexpected files; on `main`)
- [x] Initial commit baseline: `chore: initialize project structure`

## 9. Current task

None — waiting for Phase 2 instructions.

## 10. Known limitations

- No training code, API, DB, or UI yet.
- Upstream AutoResearch (reference) uses ClimbMix / large defaults; our TinyStories adaptation is deferred to Phase 2.
- Upstream `train.py` does not appear to persist checkpoints; Phase 2+ must add minimal checkpoint export for eval/inference.
- Empty dirs currently tracked via `.gitkeep`.

## 11. Next planned tasks

1. **Phase 2:** Vendor AutoResearch into `training/`, adapt to TinyStories + Colab-scale parameters in one controlled change set; keep prepare/train/program roles; minimal checkpoint save if needed for later eval/inference.
2. **Phase 3:** Postgres schema + FastAPI experiment/metrics/checkpoint APIs.
3. **Phase 4:** Colab/scripts registration path (train → parse summary → register).
4. **Phases 5–7:** Dashboard, progress/compare/models, manual eval + inference.

## 12. Important commands

```bash
# Repo root
git status
```

No app/train commands yet.

## 13. Important environment variables

None yet. (Later: Supabase/DB URL, API URLs, Colab upload credentials — document when introduced.)

## 14. Decisions that should not be accidentally changed

- Do not claim AI/Cursor/agent authorship anywhere in the project.
- Do not fork Karpathy repo as this project’s git root; training code is integrated under `training/`.
- Do not introduce ClimbMix as an intermediate training setup.
- Do not add MLflow / heavy infra in MVP.
- Do not create extra living docs (`ARCHITECTURE.md`, `TODO.md`, etc.).
- Primary metric remains `val_bpb`.
- GPU stays on Colab (or equivalent worker), not assumed on the dashboard host.
- Work in phases; stop and wait after each phase.
