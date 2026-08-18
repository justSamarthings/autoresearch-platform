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
  └── FastAPI + Postgres (Supabase)     [Phase 3+]
        ↑ register metrics / checkpoints / eval / inference
Google Colab (GPU worker)
  └── training/ (AutoResearch + TinyStories)   [Phase 2]
        → artifacts/checkpoints/*.pt
        → artifacts/results/*.json
```

GPU execution is decoupled from the web app. Single-GPU only for MVP.

## 3. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js, React, TypeScript (planned) |
| Backend | Python, FastAPI (planned) |
| Database | PostgreSQL via Supabase (planned) |
| Training | PyTorch / CUDA, AutoResearch GPT on TinyStories |

Out of scope for MVP: NeMo, Megatron, Ray, LangChain, LangGraph, MLflow, ClickHouse, Kafka, Redis, Kubernetes.

## 4. Repository structure

```
/
├── frontend/                 # empty scaffold
├── backend/                  # empty scaffold
├── training/
│   ├── prepare.py            # TinyStories prep, tokenizer, dataloader, evaluate_bpb
│   ├── train.py              # model, optimizer, loop, checkpoint, result JSON
│   ├── program.md            # agent instructions
│   ├── requirements.txt      # Colab pip deps (torch from Colab)
│   ├── pyproject.toml
│   └── artifacts/            # gitignored: checkpoints/, results/
├── scripts/
│   ├── colab_train.ipynb
│   ├── print_colab_workflow.py
│   └── verify_checkpoint.py
├── tests/
│   └── test_training_config.py
├── .gitignore
└── PROJECT_CONTEXT.md
```

## 5. Database schema

Not implemented (Phase 3). Planned: experiments, experiment_metrics, checkpoints, evaluations, inference_runs.

## 6. Important design decisions

- Own git root (not a Karpathy fork). Training vendored under `training/`.
- TinyStories (not ClimbMix) in one controlled Phase 2 adaptation.
- Primary metric remains **val_bpb** (lower is better).
- Attention: try FlashAttention3 via `kernels` when available; else PyTorch SDPA (Colab T4-friendly). Default `WINDOW_PATTERN="L"` so SDPA matches full causal attention.
- `train.py` requires CUDA; prepare/tokenizer do not.
- App server must not assume a local GPU.
- Single living context file: this file only.

## 7. Current implementation status

**Phase 2 complete (training foundation).** No FastAPI/DB/frontend yet.

## 8. Completed tasks

- [x] Task 0 inspection
- [x] Phase 1 scaffold + initial commit `9192510` + GitHub remote
- [x] Phase 2: TinyStories AutoResearch under `training/`, Colab workflow, checkpoint + result JSON, config tests

## 9. Current task

None — waiting for Phase 3 instructions.

## 10. Known limitations

- Full 5-minute GPU train / TinyStories download / CUDA pipeline **not executed in this local Windows environment** (no CUDA; dependency install blocked here). Verify on Colab via `scripts/colab_train.ipynb`.
- Local checks run: file layout, syntax parse, batch-config unit tests.
- `mfu_percent` still uses upstream H100 peak FLOPs reference (comparative only on Colab).
- SDPA path does not implement sliding-window `"S"` exactly; keep `"L"` on Colab unless FA3 works.
- No platform registration of results yet (Phase 3/4).

## 11. Next planned tasks

1. **Phase 3:** Postgres schema + FastAPI APIs for experiments/metrics/checkpoints.
2. **Phase 4:** Colab → register result JSON / checkpoint metadata with the API.
3. **Phases 5–7:** Dashboard, compare/progress, manual eval + inference.

## 12. Important commands

```bash
# Config sanity (no GPU)
python tests/test_training_config.py

# Colab / GPU machine
cd training
pip install -r requirements.txt
python prepare.py                          # TinyStories + tokenizer
python train.py                            # TIME_BUDGET=300 default
AUTORESEARCH_TIME_BUDGET=30 AUTORESEARCH_NO_COMPILE=1 python train.py   # smoke
python ../scripts/verify_checkpoint.py artifacts/checkpoints/<id>.pt
```

Notebook: `scripts/colab_train.ipynb`

## 13. Important environment variables

| Variable | Purpose |
|----------|---------|
| `AUTORESEARCH_CACHE` | Override cache dir (default `~/.cache/autoresearch-platform`) |
| `AUTORESEARCH_TIME_BUDGET` | Override training seconds (default 300 from prepare.py) |
| `AUTORESEARCH_NO_COMPILE` | Set `1` to skip `torch.compile` (faster smoke) |
| `AUTORESEARCH_EXPERIMENT_ID` | Optional fixed experiment id |

## 14. Training configuration (Phase 2 defaults)

| Setting | Value | Where |
|---------|-------|--------|
| Dataset | `karpathy/tinystories-gpt4-clean` → `train.parquet` / `val.parquet` | prepare.py |
| `MAX_SEQ_LEN` | 256 | prepare.py |
| `VOCAB_SIZE` | 1024 | prepare.py |
| `TIME_BUDGET` | 300 | prepare.py |
| `EVAL_TOKENS` | 65536 | prepare.py |
| `DEPTH` | 4 | train.py |
| `WINDOW_PATTERN` | `"L"` | train.py |
| `DEVICE_BATCH_SIZE` | 32 | train.py |
| `TOTAL_BATCH_SIZE` | 2**14 (16384) | train.py |
| Model dim | depth×64 → aligned to HEAD_DIM 128 → **256**, **2 heads** | train.py |

Batch invariant: `TOTAL_BATCH_SIZE % (DEVICE_BATCH_SIZE * MAX_SEQ_LEN) == 0` → 16384 % 8192 == 0.

### Checkpoint format

`training/artifacts/checkpoints/<experiment_id>.pt` — PyTorch dict with:

- `model_state_dict`
- `config` (GPTConfig fields)
- `meta` (experiment_id, git_commit, git_dirty, val_bpb, …)

### Result JSON

`training/artifacts/results/<experiment_id>.json` — real run fields including `val_bpb`, timings, VRAM, tokens/steps/params, depth, git_commit/dirty, checkpoint_path, configuration.

## 15. Decisions that should not be accidentally changed

- Do not claim AI/Cursor/agent authorship anywhere.
- Do not fork Karpathy as this repo root; keep code under `training/`.
- Do not reintroduce ClimbMix as the MVP dataset.
- Do not replace `val_bpb` as the primary metric.
- Do not add MLflow / heavy infra in MVP.
- Do not create extra living docs beyond this file.
- GPU stays on Colab (or equivalent worker).
- Work in phases; stop after each phase.
